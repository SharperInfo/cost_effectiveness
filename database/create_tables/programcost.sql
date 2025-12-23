create table program_cost (
pa text,
prgid text,
claimyearquarter text,
prgyear integer,
admincostother numeric,
admincostsoverheadandga numeric,
costsrecoveredfromothersources numeric,
diactivity numeric,
dihardwareandmaterials numeric,
diinstallation numeric,
direbateandinspection numeric,
emv numeric,
marketingoutreach numeric,
onbillfinancing numeric,
userinputincentive numeric,
primary key (prgid, prgyear)
);