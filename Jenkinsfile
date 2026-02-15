pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins-sa
  containers:
  - name: kaniko
    image: gcr.io/kaniko-project/executor:latest
    tty: true
	
	
  - name: helm
    image: alpine/helm:3.12.0
    command:
    - cat
    tty: true
"""
        }
    }

    environment {
        IMAGE_NAME = "registry:5000/market-forecast"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        NAMESPACE = "market-forecast"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and Push Image (Kaniko)') {
            steps {
                container('kaniko') {
                    sh """
                    /kaniko/executor \
                      --context `pwd` \
                      --dockerfile Dockerfile \
                      --destination=$IMAGE_NAME:$IMAGE_TAG \
                      --insecure \
                      --skip-tls-verify
                    """
                }
            }
        }

        stage('Deploy with Helm') {
            steps {
                container('helm') {
                    sh """
                    helm upgrade nifty ./nifty \
                      --set image.repository=$IMAGE_NAME \
                      --set image.tag=$IMAGE_TAG \
                      -n $NAMESPACE
                    """
                }
            }
        }
    }
}
