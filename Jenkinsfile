pipeline {
  agent {
    kubernetes {
      yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: docker
    image: docker:24
    command:
    - cat
    tty: true
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run/docker.sock
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
"""
    }
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
          sh 'docker build -t market-forecast:latest .'
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        container('docker') {
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
}
