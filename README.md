# ** Bundle Factory **
# Dependencies
Python 3.11.9 \
React 18.3.1

# Clone Repository
Open Mac terminal or Windows command line and clone the repository by copying and entering the line below:
```
git clone https://github.com/lgastaldi3/BundleFactory
```

# Install Dependencies
Once imported, navigate to the backend folder in the Terminal with the below:
```
cd BundleFactory
pip install -r PromoBuilderAPI/requirements.txt
cd PromoBuilderUI
Npm install
```

# Run the Application Back End
In a terminal tab, from the BundleFactory folder, enter the following. This may take a few seconds to run.
```
cd PromoBuilderAPI
python3.11 app.py
```

# Run Keegan's Combo Store Backend to retrieve development set data from Elite Reseller data at the website below with the instructions included.
Can be found at https://github.com/keeganasmith/joebob
Once all dependencies have been installed, per the joebob instructions, run the code snippet below in a separate terminal window.
```
cd backend
python3 main.py
```

# Run the Application Front End
In a separate terminal tab from the Bundle Factory folder, enter the following. This will open a webpage on localhost with which you can interact with the platform.
```
cd PromoBuilderUI
npm start
```

# Using the Tool
On the 'Bundle Creator' page, you can specify discount ranges, the number of SKUs to include, and which development set for which to create the bundles.

Clicking 'Create Table' and 'Create Images' at the top will update the BundleFactory.xlsx Excel Table for the selected development set with the bundles that are visible on the screen, using the parameters entered on the top right.

Clicking 'Generate All Tables' will update the Excel tables in BundleFactory.xlsx for all of the development sets given the number of SKUs and discount information. This may take a few minutes depending on the number of SKUs selected.

Clicking 'Generate All Images' will generate the bundle images for all of the development sets given the number of SKUs and the discount information. This can take several minutes depending on how many SKUs you are using. Please keep the process running until it completes.

