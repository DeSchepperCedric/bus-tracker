from flask import Flask
from flask import render_template

from flask_restful import Api

from config import *

from stops import Stops
from route import Route
from buses import Buses

app = Flask(__name__)
api = Api(app)


@app.route('/')
def index():
    return render_template('main-page.html', here_app_id=HERE_APP_ID, here_app_code=HERE_APP_CODE)


# Setup the Api resource routing here
api.add_resource(Route, '/api/route/<province>/<int:line_number>/<direction>',
                 resource_class_kwargs={'subscription_key': DL_SUBSCRIPTION_KEY,
                                        'here_app_id': HERE_APP_ID, 'here_app_code': HERE_APP_CODE})

api.add_resource(Stops, '/api/stops/<province>/<int:line_number>/<direction>',
                 resource_class_kwargs={'subscription_key': DL_SUBSCRIPTION_KEY,
                                        'here_app_id': HERE_APP_ID, 'here_app_code': HERE_APP_CODE})

api.add_resource(Buses, '/api/buses/<province>/<int:line_number>/<direction>',
                 resource_class_kwargs={'subscription_key': DL_SUBSCRIPTION_KEY,
                                        'here_app_id': HERE_APP_ID, 'here_app_code': HERE_APP_CODE})


if __name__ == '__main__':
    app.run(debug=True)
