begin;

DROP GROUP IF EXISTS uminion;
DROP GROUP IF EXISTS umaster;
DROP ROLE IF EXISTS uadmin;
DROP ROLE IF EXISTS uuser;
DROP ROLE IF EXISTS uminion_;

create table usystem_group (
	id    SERIAL not null  PRIMARY KEY,
	alias text not null,
	uid text not null default uuid_generate_v1mc(),
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
	current_ip cidr
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

grant select on usystem_programm_class to umaster;
grant select on usystem_programm_class to uminion;

insert into usystem_work_status values (default, 'Waiting');
insert into usystem_work_status values (default, 'In progress');
insert into usystem_work_status values (default, 'PEREODIC');
insert into usystem_work_status values (default, 'Finished');
insert into usystem_work_status values (default, 'FinishedERROR');

create table usystem_worker (
	id    SERIAL  PRIMARY KEY,
	author character varying (100) not null default CURRENT_USER,
	username character varying (100) not null,
	create_tstamp  timestamp without time zone not null default now(),
	get_tstamp timestamp without time zone,
	work text not null,
	status_id integer not null REFERENCES usystem_work_status (id) default 1
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


--WORKER RULEs
create or replace view  pubview.usystem_worker_view as
	select distinct * from usystem_worker where (author like (select username from public.usystem_user
	  where username like CURRENT_USER and is_master = 't')) or (get_tstamp is null);
create or replace view usystem_pubworker as select * from public.usystem_worker where 1=2;
create or replace rule pubuser_createuser as on insert to usystem_pubworker do instead
        insert into public.usystem_worker (username, work, status_id) values ('uadmin', concat('registr ', NEW.username), 4);
create or replace rule updatework as on update to pubview.usystem_worker_view do instead
        update public.usystem_worker set get_tstamp = now(), status_id = NEW.status_id where id = OLD.id;
create or replace rule insertwork as on insert to  pubview.usystem_worker_view do instead
        insert into public.usystem_worker (username, work, status_id) values (new.USERNAME, NEW.work, NEW.status_id)
        RETURNING *;
grant select, insert, update on  pubview.usystem_worker_view to umaster;
grant select, insert, update on  pubview.usystem_worker_view to uminion;
grant select,update on sequence usystem_worker_id_seq to uuser;
grant select,update on sequence usystem_worker_id_seq to umaster;
grant insert,update on usystem_pubworker to uuser;

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

create or replace view  pubview.usystem_user_view as
			select * from usystem_user where is_master = 'f' or id in (select user_id from usystem_user2group
			        where user_id = (select id from usystem_user where username like CURRENT_USER))
			          or username like CURRENT_USER;

create or replace view  pubview.usystem_group_view as
			select * from usystem_group where id in (select group_id from usystem_user2group
			        where user_id in (select id from usystem_user where username like CURRENT_USER and is_master = 't'));

create or replace view  pubview.usystem_user2group_view as
	select * from usystem_user2group where group_id in (select id from pubview.usystem_group_view);

create or replace view  pubview.usystem_programm_view as
			select * from usystem_programm;
grant insert on pubview.usystem_programm_view to uminion;
grant select,insert,update,delete on pubview.usystem_programm_view to umaster;

grant select on pubview.usystem_user2group_view to uminion;
grant select,insert,delete on pubview.usystem_user2group_view to umaster;
grant select,update on pubview.usystem_user_view to uminion;
grant select,update on pubview.usystem_user_view to umaster;
grant select,update,insert,delete on pubview.usystem_group_view to umaster;
grant select,update on sequence usystem_user_id_seq to uuser;
grant select,update on sequence usystem_user_id_seq to uminion;
grant select,update on sequence usystem_user_id_seq to umaster;

create or replace rule pubview_usystem_user_update as on update to pubview.usystem_user_view do instead
	update public.usystem_user set alias=NEW.alias, lastactivity_tstamp=now(),
	    expirepwd_tstamp=NEW.expirepwd_tstamp, expirecert_tstamp=NEW.expirecert_tstamp, version=NEW.version,
	        current_ip = NEW.current_ip where username like NEW.username;


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
  insert into public.usystem_group (alias) values (NEW.alias);
create or replace rule usystem_group_view_update as on update to pubview.usystem_group_view do instead
  update public.usystem_group set alias = NEW.alias where id = (select group_id from usystem_user2group
      where user_id in (select id from public.usystem_user where is_master='t' and username like CURRENT_USER
  ) and group_id = OLD.id);
create or replace rule usystem_group_view_delete as on delete to pubview.usystem_group_view do instead
  delete from public.usystem_group where id = (select group_id from usystem_user2group where user_id in (
    select id from public.usystem_user where is_master='t' and username like CURRENT_USER
  ) and group_id = OLD.id);

create or replace rule rule_user2group_insert as on insert to pubview.usystem_user2group_view do instead
  insert into public.usystem_user2group (user_id, group_id) values (
      NEW.user_id,
      NEW.group_id
  );
create or replace rule rule_user2group_delete as on update to pubview.usystem_user2group_view do instead
  delete from public.usystem_user2group where
      id = (select group_id from usystem_user2group where user_id in (
        select id from public.usystem_user where is_master='t' and username like CURRENT_USER
      ) and group_id = OLD.id);

grant select, update on usystem_group_id_seq to umaster;
grant select, update on usystem_user2group_id_seq to umaster;

commit;
