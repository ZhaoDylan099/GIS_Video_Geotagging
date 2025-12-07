create table recordings (
	audioID serial primary key,
	time_s int not null,
	transcript text not null,
	audio bytea not null,
	sample_rate int not null,
	channels int not null
)

create table embedding (

	audioID serial primary key,
	time_s int not null,
	transcript text not null,
	embedding VECTOR(384) not null
	
)