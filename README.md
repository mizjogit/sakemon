sakemon
=======

Sake Raspi Monitor

-- conversion from schema v1 to v2
-- new table sensors
-- requests, updates and inserts  are now done with a 'label'. A short unique sensor name.
-- and not a number

    drop table data60;
    drop table data600;
    drop table data3600;
    drop table data86400;
    alter table data add column probe_label varchar(20);
    update data set probe_label = 'FEXT' where probe_number = 0;
    update data set probe_label = 'FINT' where probe_number = 1;
    update data set probe_label = 'KOJI' where probe_number = 2;
    update data set probe_label = 'RH' where probe_number = 3;


-- this may not work. Depends on your schema
    alter table data drop primary key, add primary key(probe_label, timestamp);
-- if it does not do these anyway
    alter table data drop column probe_number;
    alter table data add key(probe_label, timestamp);

#back in the shell create the tables
    ./sakidb.py --create

./gmonit 
