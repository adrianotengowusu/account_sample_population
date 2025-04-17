# account_sample_population
This script enables you to reference an XML product feed and create dummy data based on the products in the feed.


Pre-requisites:
You will need to ensure that you have created your product feed in XML format. The feilds required for the default feed execution are;
* id
* title
* price
* category
* url
* image_url
* inventory
* rating

However, you can always customise this and modify the load_products_from_xml and properties array in the send_event function


Execution:
Ensure that the XML file is located in the same directory as the python script and run the following command:
python3 create_profile_events.py
