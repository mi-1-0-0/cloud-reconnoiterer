from neo4jresource import app
import os

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
