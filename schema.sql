drop table if exists member;
create table member (
	id integer primary key autoincrement,
	name text not null,
	email text not null,
	successes integer,
	misses integer,
	join_date integer,
	active boolean
);

drop table if exists clique;
create table clique (
	id integer primary key autoincrement,
	start_date integer,
	end_date integer
);

drop table if exists membership;
create table membership (
	member_id integer,
	clique_id integer,
	completed boolean,
	active boolean
);

drop table if exists lunch;
create table lunch (
	clique_id integer,
	member_one integer,
	member_two integer,
	completed boolean
);
