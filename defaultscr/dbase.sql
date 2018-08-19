CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP GROUP IF EXISTS uminion;
DROP GROUP IF EXISTS umaster;
DROP ROLE IF EXISTS uadmin;
DROP ROLE IF EXISTS uuser;
DROP ROLE IF EXISTS uminion_;
begin;

create table usystem_group (
	id    SERIAL not null  PRIMARY KEY,
	alias text not null,
	author character varying(100) not null default CURRENT_USER,
	uid text not null default uuid_generate_v1mc(),
	parent_id integer,
	path text not null default '';
	create_tstamp timestamp without time zone not null default now()
);

create table usystem_user (
	id    SERIAL not null  PRIMARY KEY,
	username character varying(100) unique not null,
	alias text,
	email text,
	register_tstamp timestamp without time zone not null default now(),
	lastactivity_tstamp timestamp without time zone not null default now(),
	email_confirmed boolean not null default 'f',
	is_master boolean not null default 'f',
	expirepwd_tstamp timestamp without time zone not null default now() + INTERVAL '90 DAY',
	expirecert_tstamp timestamp without time zone not null default now(),
	home_path text not null default '/home/',
	version character varying(100) not null default '0.0',
	current_ip cidr,
	policy integer not null default 0
);

create table usystem_user2group (
        id    SERIAL  PRIMARY KEY,
	      user_id integer not null REFERENCES usystem_user (id) on delete cascade,
	      group_id integer not null REFERENCES usystem_group (id)  on delete cascade
);

create table usystem_work_status (
        id    SERIAL not null  PRIMARY KEY,
	      name text not null
);

create table usystem_programm_class (
        id    SERIAL not null  PRIMARY KEY,
	      name text not null
);

insert into usystem_programm_class values (default, 'OS');

create table usystem_programm (
        id    SERIAL  PRIMARY KEY,
	      username character varying(100) not null,
	      classname_id integer not null REFERENCES usystem_programm_class (id)  on delete cascade,
	      name character varying(100) not null
);

insert into usystem_work_status values (default, 'Waiting');
insert into usystem_work_status values (default, 'In progress');
insert into usystem_work_status values (default, 'PEREODIC');
insert into usystem_work_status values (default, 'Finished');
insert into usystem_work_status values (default, 'FinishedERROR');
insert into usystem_work_status values (default, 'Closed');

create table usystem_worker (
	id    SERIAL  PRIMARY KEY,
	author character varying (100) not null default CURRENT_USER,
	username character varying (100) not null,
	create_tstamp  timestamp without time zone not null default now(),
	get_tstamp timestamp without time zone,
	work text not null,
	status_id integer not null REFERENCES usystem_work_status (id) default 1
);


create table usystem_portmap (
  id    SERIAL  PRIMARY KEY,
  work_id integer not null REFERENCES usystem_worker (id),
  port_num integer not null
);


create table usystem_log_action (
        id    SERIAL PRIMARY KEY,
	action_name text not null
);

create table usystem_log (
        id    SERIAL  PRIMARY KEY,
        author character varying (100) not null default CURRENT_USER,
        create_tstamp  timestamp without time zone not null default now(),
	action_id integer not null REFERENCES usystem_log_action (id),
	comment text not null
);

create role uminion_ login;
CREATE GROUP umaster;
CREATE GROUP uminion;
alter group uminion add user uminion_;
grant select on usystem_work_status to uminion;
grant select on usystem_work_status to umaster;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
create role uadmin login;
create role uuser login;
create schema uadmin;
create schema pubview;
grant usage on schema uadmin to uadmin;
grant usage on schema pubview to umaster;
grant usage on schema pubview to uminion;


--LOGGING RULEs
grant select on usystem_log_action to uminion;
grant select on usystem_log_action to umaster;
create or replace view  pubview.usystem_log_view as select * from usystem_log where author like CURRENT_USER;
grant select, insert on  pubview.usystem_log_view to umaster;
grant select, insert on  pubview.usystem_log_view to uminion;


--REGISTER RULE
create or replace view usystem_pubuser as select username, email from usystem_user;
grant select, insert, update on usystem_pubuser to uuser;
grant select, insert on usystem_pubuser to uminion;
create or replace rule pubuser_registration as on insert to usystem_pubuser do instead
	insert into public.usystem_user (username, email)
		values (NEW.username, NEW.email);
create or replace rule pubuser_confirm as on update to usystem_pubuser do instead
	update public.usystem_user set is_master='t', email_confirmed='t', home_path = concat('/home/', OLD.username) where username like NEW.username;


--USERs RULEs

create or replace view  pubview.usystem_group_view as
			select * from usystem_group where author like CURRENT_USER or id in (select group_id from usystem_user2group
			        where user_id in (select id from usystem_user where username like CURRENT_USER and is_master = 't'
			          or is_master = 'f'));

create or replace view  pubview.usystem_user2group_view as
	select * from usystem_user2group where group_id in (select id from pubview.usystem_group_view);

create or replace view  pubview.usystem_user_view as
			select * from usystem_user where is_master = 'f' or username like CURRENT_USER or id in
			  (select user_id from pubview.usystem_user2group_view);


create or replace view  pubview.usystem_programm_view as
			select * from usystem_programm;
grant insert on pubview.usystem_programm_view to uminion;
grant select,insert,update,delete on pubview.usystem_programm_view to umaster;

grant select,delete on pubview.usystem_user2group_view to uminion;

grant select,insert,delete on pubview.usystem_user2group_view to umaster;
grant select,update on pubview.usystem_user_view to uminion;
grant select,update on pubview.usystem_user_view to umaster;
grant select,update,insert,delete on pubview.usystem_group_view to umaster;
grant select,update on sequence usystem_user_id_seq to uuser;
grant select,update on sequence usystem_user_id_seq to uminion;
grant select,update on sequence usystem_user_id_seq to umaster;

create or replace rule pubview_usystem_user_update as on update to pubview.usystem_user_view do instead
	update public.usystem_user set alias=NEW.alias, lastactivity_tstamp=now(), policy=NEW.policy,
	    expirepwd_tstamp=NEW.expirepwd_tstamp, expirecert_tstamp=NEW.expirecert_tstamp, version=NEW.version,
	        current_ip = NEW.current_ip where username like NEW.username;


--WORKER RULEs
create or replace view  pubview.usystem_worker_view as
	select * from usystem_worker where (author like (select username from public.usystem_user
	  where username like CURRENT_USER and is_master = 't')) or (status_id <= 4);
create or replace view usystem_pubworker as select * from public.usystem_worker where 1=2;
create or replace rule pubuser_createuser as on insert to usystem_pubworker do instead
        insert into public.usystem_worker (username, work, status_id) values ('uadmin', concat('registr ', NEW.username), 4);
create or replace rule updatework as on update to pubview.usystem_worker_view do instead
        update public.usystem_worker set get_tstamp = now(), status_id = NEW.status_id,
          work=(
                  case (select count(*) from pubview.usystem_worker_view where id = OLD.id and work = '') when 1 then NEW.work
                  else OLD.work
                  end
               )
            where id = OLD.id;

create or replace rule insertwork as on insert to  pubview.usystem_worker_view do instead
        insert into public.usystem_worker (username, work, status_id) values (new.USERNAME, NEW.work, NEW.status_id)
        RETURNING *;
grant select, insert, update on  pubview.usystem_worker_view to umaster;
grant select, insert, update on  pubview.usystem_worker_view to uminion;
grant select,update on sequence usystem_worker_id_seq to uuser;
grant select,update on sequence usystem_worker_id_seq to umaster;
grant select,update on sequence usystem_worker_id_seq to uminion;
grant insert,update on usystem_pubworker to uuser;


--MAP RULEs
create or replace view pubview.usystem_portmap_view as select * from usystem_portmap;
grant select, insert, delete on  pubview.usystem_portmap_view to umaster;
grant select, insert, delete on  pubview.usystem_portmap_view to uminion;
create or replace rule usystem_portmap_view_insert as on insert to pubview.usystem_portmap_view do instead
    insert into public.usystem_portmap (work_id, port_num)
		    values ((select id from pubview.usystem_worker_view where id = NEW.work_id), NEW.port_num) returning *;
create or replace rule usystem_portmap_view_delete as on delete to pubview.usystem_portmap_view do instead
    delete from public.usystem_portmap where
		    work_id in (select id from pubview.usystem_worker_view) and id = OLD.id;

grant select, update on usystem_portmap_id_seq to umaster;
grant select, update on usystem_portmap_id_seq to uminion;

--programm rule
grant select,update on sequence usystem_programm_id_seq to umaster;
grant select,update on sequence usystem_programm_id_seq to uminion;
create or replace rule pubview_usystem_programm_insert as on insert to pubview.usystem_programm_view do instead
	insert into public.usystem_programm (username, classname_id, name)
		values (NEW.username, NEW.classname_id, NEW.name);
create or replace rule pubview_usystem_programm_update as on update to pubview.usystem_programm_view do instead
	update public.usystem_programm set username=NEW.username, classname_id=NEW.classname_id, name=NEW.name where id= OLD.id;
create or replace rule pubview_usystem_programm_delete as on delete to pubview.usystem_programm_view do instead
  delete from public.usystem_programm where id= OLD.id;


--GROUP RULES
create or replace rule usystem_group_view_create as on insert to pubview.usystem_group_view do instead
  insert into public.usystem_group (alias, parent_id) values (NEW.alias,
                  (select id from pubview.usystem_group_view where id = NEW.id)) returning *;
create or replace rule usystem_group_view_update as on update to pubview.usystem_group_view do instead
  update public.usystem_group set alias = NEW.alias, path=NEW.path, parent_id=NEW.parent_id where id = (select group_id from usystem_user2group
      where user_id in (select id from public.usystem_user where is_master='t' and username like CURRENT_USER
  ) and group_id = OLD.id);

create or replace rule usystem_group_view_delete as on delete to pubview.usystem_group_view do instead
  delete from public.usystem_group where (author like CURRENT_USER or id in (select group_id from usystem_user2group where user_id in (
    select id from public.usystem_user where is_master='t' and username like CURRENT_USER
  ))) and id = OLD.id and alias != 'Ожидают авторизации';

create or replace rule rule_user2group_insert as on insert to pubview.usystem_user2group_view do instead
  insert into public.usystem_user2group (user_id, group_id) values (
      NEW.user_id,
      NEW.group_id
  ) returning *;

create or replace rule rule_user2group_delete as on delete to pubview.usystem_user2group_view do instead
  delete from public.usystem_user2group where
      user_id in (
        select id from public.usystem_user where is_master='t' and username like CURRENT_USER or is_master='f'
      ) and user_id = OLD.user_id;

grant select, update on usystem_group_id_seq to umaster;
grant select, update on usystem_user2group_id_seq to umaster;

grant select on usystem_programm_class to umaster;
grant select on usystem_programm_class to uminion;
commit;
