pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "localhost:5000/market-forecast"
        NAMESPACE = "market-forecast"
        DEPLOYMENT = "market-forecast"
        TRAIN_CRON = "nifty-train-job"
        UPDATE_CRON = "nifty-update-job"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} .
                """
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                    docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
                    docker logout
                    """
                }
            }
        }

        stage('Update Kubernetes Deployment') {
            steps {
                sh """
                kubectl set image deployment/${DEPLOYMENT} \
                ${DEPLOYMENT}=${DOCKER_IMAGE}:${IMAGE_TAG} \
                -n ${NAMESPACE}
                """
            }
        }

        stage('Update Kubernetes CronJobs') {
            steps {
                sh """
                kubectl set image cronjob/${TRAIN_CRON} \
                ${TRAIN_CRON}=${DOCKER_IMAGE}:${IMAGE_TAG} \
                -n ${NAMESPACE}

                kubectl set image cronjob/${UPDATE_CRON} \
                ${UPDATE_CRON}=${DOCKER_IMAGE}:${IMAGE_TAG} \
                -n ${NAMESPACE}
                """
            }
        }

        stage('Verify Rollout') {
            steps {
                sh """
                kubectl rollout status deployment/${DEPLOYMENT} -n ${NAMESPACE}
                """
            }
        }
    }

    post {
        success {
            echo "Deployment successful 🚀 Image tag: ${IMAGE_TAG}"
        }
        failure {
            echo "Build or Deployment Failed ❌"
        }
    }
}
