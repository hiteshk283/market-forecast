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
    IMAGE = "localhost:5000/market-forecast"
    TAG = "${env.BUILD_NUMBER}"
    NAMESPACE = "market-forecast"
  }

  stages {

    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build & Push') {
      steps {
        container('docker') {
          sh """
            docker build -t $IMAGE:$TAG .
            docker push $IMAGE:$TAG
          """
        }
      }
    }

    stage('Deploy') {
      steps {
        container('helm') {
          sh """
            helm upgrade --install nifty ./nifty \
              --set image.repository=$IMAGE \
              --set image.tag=$TAG \
              --set image.pullPolicy=Always \
              -n $NAMESPACE --create-namespace
          """
        }
      }
    }
  }
}
