pipeline {
    agent any

    environment {
        IMAGE_NAME = "localhost:5000/market-forecast"
        IMAGE_TAG = "latest"
        NAMESPACE = "market-forecast"
    }

    stages {
        stage('Deploy with Helm') {
            steps {
                sh """
                helm upgrade --install nifty ./nifty \
                  --set image.repository=$IMAGE_NAME \
                  --set image.tag=$IMAGE_TAG \
                  --set image.pullPolicy=Always \
                  -n $NAMESPACE \
                  --create-namespace
                """
            }
        }
    }
}
