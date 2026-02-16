pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins-sa

  containers:
  - name: docker
    image: docker:24
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
        IMAGE_NAME = "registry.market-forecast.svc.cluster.local:5000/market-forecast"
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        NAMESPACE = "market-forecast"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Image') {
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
}
