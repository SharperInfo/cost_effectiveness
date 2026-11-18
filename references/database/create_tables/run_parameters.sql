create table run_parameters (
parameter text primary key,
value numeric
);

insert into run_parameters (parameter, value)
values 
('market_effect', 0.05),
('calculation_version', 1.0),
('avoided_cost_version', 2026),
('first_year', 2026),