create table recordings (
	audioID serial primary key,
	time_s int not null,
	audio bytea not null,
	sample_rate int not null,
	channels int not null
)