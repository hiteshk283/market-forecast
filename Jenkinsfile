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
    image: gcr.io/kaniko-project/executor:debug
    command:
    - cat
    tty: true
    resources:
      requests:
        memory: "1Gi"
        cpu: "500m"
      limits:
        memory: "3Gi"
        cpu: "1"


  - name: helm
    image: alpine/helm:3.12.0
    command:
    - cat
    tty: true
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

        stage('Build & Push Image (Kaniko)') {
            steps {
                container('kaniko') {
                    sh """
                    /kaniko/executor \
                      --context `pwd` \
                      --dockerfile Dockerfile \
                      --destination=$IMAGE_NAME:$IMAGE_TAG \
					  --snapshot-mode=redo \
                      --insecure \
                      --skip-tls-verify \
                      --skip-tls-verify-registry registry:5000
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
                      -n $NAMESPACE \
                      --create-namespace
                    """
                }
            }
        }
    }
}
