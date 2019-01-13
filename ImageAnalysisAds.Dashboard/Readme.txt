(Optional) Config virtual enviornment
0.1 Install package
pip install virtualenv

0.2 Navigate to the "ImageAnalysisAds.Dashboard" folder to create a virtual environment
virtual venv

0.3 Activate virtual environment
venv\scripts\activate

-- in case need to deavtivate the virtual environment
deactivate

0.4 Output requirements.txt
pip freeze > requirements.txt

---------------------------------------------
1. Install required Python packages:
From command line prompt navigate to "ImageAnalysisAds.Dashboard" repository and run the command: 
(You can do it in virtual enviornment or not)
> pip install -r requirements.txt

2. Run the dashboard application:
> python run.py

3. Launch Kim's Object Detection API and Huaipeng's API:
https://github.com/kdung/ImageAnalysisAds/wiki/how-to-test-serving-api

4. Ready to test!

Caution:
- DB data is static
DB file is in ImageAnalysisAds.Dashboard\db folder, since it's local, the data inside will be different for every person.
We need to create some 'nice' data for presentation, but before that, please test and DON'T commit your changes of the db file
Current accounts:
admin, test, michael, tom, marry; passwords are same; if you login in as admin, the GUI will be different with other accounts

- Image locations:
Original Image: ImageAnalysisAds.Dashboard\app\base\static\images\img_origin
Framed Image: ImageAnalysisAds.Dashboard\app\base\static\images\img_framed
Result Image: ImageAnalysisAds.Dashboard\app\base\static\images\img_result
Labels: ImageAnalysisAds.Dashboard\app\base\static\images\label
I have uploaded some testing files allowing you to look and feel; Also the images will be different too as they are local
Don't commit your images after testing.

- If needs to access the database.db file:
> https://www.youtube.com/watch?v=wXEZZ2JT3-k
> Install https://sqlitebrowser.org/ GUI tool to view the data

