from flask import Flask , request, render_template, jsonify 
from src.pipeline.prediction_pipeline import CustomData, PredictPipeline
from src.components.data_injestion import DataIngestion
from src.components.data_transformation import DataTransformation
from src.components.model_trainer import ModelTrainer
import pandas as pd
from urllib.request import urlopen as uReq
from flask_cors import CORS,cross_origin
from bs4 import BeautifulSoup as bs
import requests

application = Flask(__name__)
app = application

@app.route('/')
def home_page():
    return render_template('index.html')

@app.route('/result')
def resultPage():
    if request.method=='GET':
        show = 'You have not run the prediction'
        return render_template('result.html', show=show)
    
@app.route('/data')
def csv_to_html():
    data = pd.read_csv("data.csv")
    data = data[:100]
    return render_template('data.html',result=[data.to_html(index=False)])

@app.route('/train')
def train_data():
    obj = DataIngestion()   
    train_data_path, test_data_path = obj.initiate_data_ingestion()
    data_transformation = DataTransformation()
    train_arr, test_arr, _ = data_transformation.initiate_data_transformation(train_data_path, test_data_path)
    model_trainer=ModelTrainer()
    model_trainer.initate_model_training(train_arr, test_arr)
    context = "Your Model is trained Successful"
    return render_template('index.html',context=context) 

@app.route('/predict', methods=['GET','POST'])
def predict():
    if request.method=='GET':
        return render_template('form.html')
    else:
        data = CustomData(
            Delivery_person_Age = float(request.form.get('Delivery_person_Age')),
            Delivery_person_Ratings = float(request.form.get('Delivery_person_Ratings')),
            Restaurant_latitude =float(request.form.get('Restaurant_latitude')),
            Restaurant_longitude = float(request.form.get('Restaurant_longitude')),
            Delivery_location_latitude = float(request.form.get('Delivery_location_latitude')),
            Delivery_location_longitude = float(request.form.get('Delivery_location_longitude')),
            Vehicle_condition = float(request.form.get('Vehicle_condition')),
            multiple_deliveries = float(request.form.get('multiple_deliveries')),
            Weather_conditions = request.form.get('Weather_conditions'),
            Road_traffic_density = request.form.get('Road_traffic_density'),     
            Type_of_order = request.form.get('Type_of_order'),     
            Type_of_vehicle = request.form.get('Type_of_vehicle'),     
            Festival = request.form.get('Festival'),     
            City = request.form.get('City')    
        )
        final_new_data = data.get_data_as_dataframe()
        predict_pipeline = PredictPipeline()
        pred = predict_pipeline.predict(final_new_data)
        results = round(pred[0],2)
        Congratulations = 'Congratulations'
        return render_template('result.html', final_result = results, Congratulations=Congratulations)


@app.route('/reviewhome',methods=['GET'])  
@cross_origin()
def homePage():
    return render_template("review_index.html")

@app.route('/review',methods=['POST','GET']) 
@cross_origin()
def reviews():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ","")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
            del bigboxes[0:3]
            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            prodRes = requests.get(productLink)
            prodRes.encoding='utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            commentboxes = prod_html.find_all('div', {'class': "_16PBlm"})
            filename = searchString + ".csv"
            fw = open(filename, "w")
            headers = "Product, Customer Name, Rating, Heading, Comment \n"
            fw.write(headers)
            reviews = []
            for commentbox in commentboxes:
                try:
                    name = commentbox.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                except:
                    name = 'No Name'
                try:
                    rating = commentbox.div.div.div.div.text
                except:
                    rating = 'No Rating'
                try:
                    commentHead = commentbox.div.div.div.p.text

                except:
                    commentHead = 'No Comment Heading'
                try:
                    comtag = commentbox.div.div.find_all('div', {'class': ''})
                    custComment = comtag[0].div.text
                except Exception as e:
                    print("Exception while creating dictionary: ",e)

                mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,
                          "Comment": custComment}
                reviews.append(mydict)

            return render_template('review_result.html', reviews=reviews[0:(len(reviews)-1)])
        except Exception as e:
            print('The Exception message is: ',e)
            return 'something is wrong'
    else:
        return render_template('review_result.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0',
            port=5000, 
            debug=True)