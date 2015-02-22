#!/usr/bin/env python

#===============#
#   Constants   #
#===============#
DB_NAME = "destinations.sqlite.db"
MAIN_TEMPLATE_FILENAME = "main_template.pt"
MISC_REGION_NAME = "Misc. Region"

#=============#
#   Imports   #
#=============#
from random import choice #for random selection
from simpletal import simpleTAL,simpleTALES #for HTML templating
import cgi #for running as a cgi-bin
import sqlite3 #for connecting to database
import sys #for outputting page templates

#=============#
#   Headers   #
#=============#
print "Content-Type: text/html" # HTML is following
print "" # blank line, end of headers

#=============#
#   Globals   #
#=============#
dbConnection = None
cursor = None

#====================#
#   Custom methods   #
#====================#
def chooseRandomCity(cities):
	""" Chooses a random city from the list """
	
	city = choice(cities)
	
	return city
def chooseRandomCountry(countries):
	""" Chooses a random country from the list """
	
	country = choice(countries)
	
	return country
def chooseRandomRegion(regions):
	""" Chooses a random state/region from the list """
	
	region = choice(regions)
	
	return region
def connectDB():
	global dbConnection
	global cursor
	
	#connect to db
	try:
		dbConnection = sqlite3.connect(DB_NAME)
	except:
		raise RuntimeError("ERROR: Unable to connect to database")
	
	#try to use row dictionaries instead of row lists
	try:
		dbConnection.row_factory = sqlite3.Row
	except:
		raise RuntimeError("ERROR: Unable to use record field names")
	
	#get cursor
	try:
		cursor = dbConnection.cursor()
	except:
		raise RuntimeError("ERROR: Unable to get database cursor")
	
	return
def convertRowsToDicts(rows):
	""" Converts a database result set into a list of dictionaries """

	listOfDicts = [dict(zip(row.keys(),row)) for row in rows]
	return listOfDicts
def disconnectDB():
	global dbConnection
	global cursor
	
	try:
		dbConnection.commit()
		dbConnection.close()
	except:
		raise RuntimeError("ERROR: Unable to close connection")
	
	return
def loadCitiesByRegion(region):
	""" loads the city into memory """
	
	#globals
	global cursor
	
	#select cities
	query = "SELECT * FROM city WHERE region_id = ? AND is_active"
	cursor.execute(query,(region["id"],))
	results = cursor.fetchall()
	
	#create a list of dicts
	cities = convertRowsToDicts(results)
	
	return cities
def loadCountries():
	""" loads the countries into memory """
	
	#globals
	global cursor
	
	#select countries
	query = "SELECT * FROM country WHERE is_active ORDER BY name"
	cursor.execute(query)
	results = cursor.fetchall()
	
	#create a list of dicts
	countries = convertRowsToDicts(results)
	
	return countries
def loadCountryByID(countryID):
	""" gets the country by its ID """

	#globals
	global cursor
	
	#select country
	query = "SELECT * FROM country WHERE `id` = ?"
	cursor.execute(query,(countryID,))
	results = cursor.fetchall()

	#create a list of dicts
	countries = convertRowsToDicts(results)

	return countries[0]
def loadRegionsByCountry(country):
	""" loads the states/regions into memory """
	
	#globals
	global cursor
	
	#select states/regions
	query = "SELECT * FROM region WHERE country_id = ? AND is_active"
	cursor.execute(query,(country["id"],))
	results = cursor.fetchall()
	
	#create a list of dicts
	regions = convertRowsToDicts(results)
	
	#check for misc. regions
	for region in regions:
		if(region["name"] == MISC_REGION_NAME):
			region["is_misc"] = True
		else:
			region["is_misc"] = False
	
	return regions
def loadPageTemplate(filename):
	""" Loads and compiles the page template """

	#create the context that is used by the template
	context = simpleTALES.Context()
	
	#load and compile the page template
	templateFile = open(filename,'rt')
	template = simpleTAL.compileHTMLTemplate(templateFile)
	templateFile.close()

	#load and compile the main template macro
	macroFile = open(MAIN_TEMPLATE_FILENAME,'rt')
	mainTemplate = simpleTAL.compileHTMLTemplate(macroFile)
	macroFile.close()

	#add main template to context
	context.addGlobal("main_template",mainTemplate)

	#return context and page template
	return (context,template)
def outputResults(form,city,region,country):
	""" Prints the randomly chosen destination """
	
	#load and compile the page template
	context,template = loadPageTemplate("pick_random_destination.view.pt")
	
	#determine full name
	if(region["is_misc"]):
		fullName = "%s, %s" % (city["name"],country["name"])
	else:
		fullName = "%s, %s, %s" % (city["name"],region["name"],country["name"])
	
	#add information
	context.addGlobal("country",country)
	context.addGlobal("region",region)
	context.addGlobal("city",city)
	context.addGlobal("full_name",fullName)
	
	#add form vars
	countryID = form.getvalue("country")
	if(countryID):
		context.addGlobal("countryID",countryID)
	
	#output the page template
	template.expand(context, sys.stdout)
	
	return

#==========#
#   Main   #
#==========#
def main():
	""" Main method """
	
	#connect to the database
	connectDB()
	
	#load database into memory
	countries = loadCountries()
	
	#load form
	form = cgi.FieldStorage()
	
	#check if form was submitted
	if(form.has_key("submit")):
		#show results
		
		#check for selected country
		chosenCountry = form.getvalue("country")
		if(chosenCountry):
			#get the country that was chosen
			country = loadCountryByID(chosenCountry)
		else:
			#choose a random country
			country = chooseRandomCountry(countries)
		
		#load states/regions
		regions = loadRegionsByCountry(country)
		
		#choose a random region
		region = chooseRandomRegion(regions)
		
		#load cities
		cities = loadCitiesByRegion(region)
		
		#choose a random city
		city = chooseRandomCity(cities)
		
		#output results
		outputResults(form,city,region,country)
	else:
		#show form
		
		#load and compile the page template
		context,template = loadPageTemplate("pick_random_destination.form.pt")

		#add information
		context.addGlobal("countries",countries)

		#output the page template
		template.expand(context, sys.stdout)
	
	#disconnect from database
	disconnectDB()

if __name__== "__main__":
	main()
