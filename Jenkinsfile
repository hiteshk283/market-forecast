pipeline {
    agent any

    environment {
        IMAGE_NAME = "nifty"
        NAMESPACE = "market-forecast"
    }

    stages {

        stage('Checkout Code') {
            steps {
                git 'https://github.com/hiteshk283/market-forecast.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE_NAME:latest .'
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh 'kubectl apply -f k8s/namespace.yaml'
                sh 'kubectl apply -f k8s/pvc.yaml'
                sh 'kubectl apply -f k8s/deployment.yaml'
                sh 'kubectl apply -f k8s/service.yaml'
                sh 'kubectl apply -f k8s/cronjob-update.yaml'
                sh 'kubectl apply -f k8s/cronjob-train.yaml'
            }
        }
    }
}
