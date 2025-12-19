# cost_effectiveness

This is a work in progress. 

## The current CPUC CET has a number of technical issues
- It can only process one input at a time
- The same calculations are done over and over in different places
- Unconventional and overengineered approach
- It is difficult to trace data through the equations because the field names change at multiple steps
- Microsoft SQL Server is required to run the database
- ToDo: add others

## Those issues impact the data reporting community
- The code is difficult to update; updates are time consuming and error prone
- The logic behind the equations is sprinkled throughout the database tables, views, funtions, and stored procedures
- ToDo: add others

## To address those issues, we want to bring the cost effectiveness calculations out of existing CET 
- Make the code publicly available and easily accessible
- Version control
- Use the same names

## Expected outcomes
- Allow more people to work directly with the calculations
- Allow CEDARS to calculate cost effectiveness internally
- Improved performamce
- New opportunities for program administrators to automate their cost effectiveness calculations

## Overall approach
- Database build scripts that create the required data tables
- Calculations in database views
