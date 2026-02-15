pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins
  containers:
  - name: docker
    image: localhost:5000/docker:24
    command:
    - cat
    tty: true
    volumeMounts:
    - name: dockersock
      mountPath: /var/run/docker.sock

  - name: helm
    image: alpine/helm:3.12.0
    command:
    - cat
    tty: true

  volumes:
  - name: dockersock
    hostPath:
      path: /var/run/docker.sock
"""
        }
    }

    environment {
        IMAGE_NAME = "10.214.238.113:5000/market-forecast"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        NAMESPACE = "market-forecast"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                container('docker') {
                    sh """
                    docker build -t $IMAGE_NAME:$IMAGE_TAG .
                    """
                }
            }
        }

        stage('Push Image') {
            steps {
                container('docker') {
                    sh """
                    docker push $IMAGE_NAME:$IMAGE_TAG
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
