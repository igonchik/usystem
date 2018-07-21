create table usystem_group (
        alias character varying(100) constraint alias_key PRIMARY KEY,
        uid text not null unique,
        ca text not null,
        crl text not null,
        create_tstamp timestamp without time zone not null default now(),
        ca_tstamp timestamp without time zone not null default now(),
        crl_tstamp timestamp without time zone not null default now()
);

create table usystem_user (
        username character varying(100) constraint username_key PRIMARY KEY,
        email text not null unique,
        uid text not null unique,
        register_tstamp timestamp without time zone not null default now(),
        lastactivity_tstamp timestamp without time zone not null default now(),
        email_confirmed boolean not null default 'f',
        is_master boolean not null default 'f',
        expirepwd_tstamp timestamp without time zone not null default now(),
        expirecert_tstamp timestamp without time zone not null default now(),
        home_path text not null default '/home/',
        public_key text unique,
        installation_tstamp timestamp without time zone
);


grant select, insert on usystem_log_view "masteruser";
grant select, insert on usystem_log_view "masteruser";
grant select on usystem_log_action to "masteruser";
