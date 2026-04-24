# Azure Pipelines:
Предварительно: 
- поднял три ВМ в VirtualBox:
    1. Основная ВМ для рабочего окружения, где ведется сама работа с репозиторием  (Desktop Ubuntu 24.04.2 LTS RAM: 4 CPU: 2) - 192.168.56.3
    2. ВМ под агента (Server Ubuntu 22.04.5 LTS RAM: 2 CPU: 1) и k3s-master - 192.168.56.5
    3. ВМ под k3s-worker (Server Ubuntu 22.04.5 LTS RAM: 2 CPU: 1) - 192.168.56.4
- установил docker на агента по официальной инструкции

Настроил на всех ВМ внутреннюю сеть:

    sudo nano /etc/netplan/01-netcfg.yaml
***
    network:
    version: 2
    renderer: networkd
    ethernets:
        enp0s8:
        dhcp4: no
        addresses:
            - 192.168.56.3/24 (этот IP разный на всех машинах см. выше)
***
    sudo netplan apply


## [Мой pipeline](https://tfs.msk.evraz.com/tfs/%D0%A2%D0%B5%D1%81%D1%82%D0%BE%D0%B2%D0%B0%D1%8F%20%D0%BA%D0%BE%D0%BB%D0%BB%D0%B5%D0%BA%D1%86%D0%B8%D1%8F/Ivan-Khodyrev/_git/hello-app?path=/azure-pipelines.yml)

## Создал собственный пул агентов [self-hosted](https://tfs.msk.evraz.com/tfs/%D0%A2%D0%B5%D1%81%D1%82%D0%BE%D0%B2%D0%B0%D1%8F%20%D0%BA%D0%BE%D0%BB%D0%BB%D0%B5%D0%BA%D1%86%D0%B8%D1%8F/Ivan-Khodyrev/_settings/agentqueues?queueId=1333&view=jobs) и подключил  [агента](https://tfs.msk.evraz.com/tfs/%D0%A2%D0%B5%D1%81%D1%82%D0%BE%D0%B2%D0%B0%D1%8F%20%D0%BA%D0%BE%D0%BB%D0%BB%D0%B5%D0%BA%D1%86%D0%B8%D1%8F/Ivan-Khodyrev/_settings/agentqueues?queueId=1333&view=agents)

## Написал на ВМ-агенте простой systemd-unit, чтобы он поддерживал агента в статусе онлайн:

    sudo nano /etc/systemd/system/azure-agent.service
***
    [Unit]
    Description="Azure Agent for pipelines"

    [Service]
    Type=simple
    User=ivan
    Group=ivan
    ExecStart=/home/ivan/azure-agent/run.sh
    Restart=always

    [Install]
    WantedBy=multi-user.target
***
    sudo systemctl daemon-reload
    sudo systemctl start azure-agent.service
    sudo systemctl enable azure-agent.service
    sudo systemctl status azure-agent.service

![image.png](/.attachments/azure-agent_is_running.png)

## Создание собственного легкого k3s-кластера

- `azure-agent01 (192.168.56.5)` - control-plane + azure-agent
- `k3s-worker (192.168.56.4)` - worker node  

Так как по непонятным причинам после установки с помощью `curl -sfL https://get.k3s.io | sh -` сервиc `k3s-agent.service` отказывался стартовать, было принято решение локально создать файл скрипта `install-k3s.sh`.  
В данный файл было скопированно содержимое [Официального скрипта](https://get.k3s.io/)  
После чего данный скрипт был запущен:
1. На `azure-agent01 (192.168.56.5)` командой `./install-k3s.sh`
2. На `k3s-worker (192.168.56.4)` командой `sudo env K3S_URL=https://192.168.56.5:6443 K3S_TOKEN="***" ./install-k3s.sh` (токен берем на `azure-agent01 (192.168.56.5)` - `sudo cat /var/lib/rancher/k3s/server/node-token`)

На `azure-agent01 (192.168.56.5)` выполняем следующие настройки, чтобы выполнять команды `kubectl` без sudo:

    sudo chmod 644 /etc/rancher/k3s/k3s.yaml
    mkdir -p ~/.kube
    sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
    sudo chown $(id -u):$(id -g) ~/.kube/config
    chmod 600 ~/.kube/config

![image.png](/.attachments/get_nodes.png)

Первоначальные настройки для нашего кластера готовы!

## Устанавливаем Helm на наш control-plane

    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    sudo chown root:root /usr/local/bin/helm
    sudo chmod 755 /usr/local/bin/helm
    sudo chown root:root /usr/local/bin/helm

## Настраиваем taints, чтобы на control plane не поднимались поды:

    kubectl taint nodes azure-agent01 node-role.kubernetes.io/control-plane:NoSchedule
## Результат сборки:

![image.png](/.attachments/build_succeeded.png)
![image.png](/.attachments/terminal192168565.png)
![image.png](/.attachments/terminal192168563.png)
![image.png](/.attachments/result_in_browser.png)
## Список источников:
1. [Что такое Azure Pipelines](https://learn.microsoft.com/ru-ru/azure/devops/pipelines/get-started/what-is-azure-pipelines?view=azure-devops)  
2. [Создание первого конвейера](https://learn.microsoft.com/ru-ru/azure/devops/pipelines/create-first-pipeline?view=azure-devops&tabs=java%2Cbrowser)
3. [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
4. [Azure DevOps Pipelines Fundamental Tutorials](https://www.devopsschool.com/blog/azure-devops-pipelines-fundamental-tutorials/)
5. [Quick-Start Guide | K3s](https://docs.k3s.io/quick-start)
6. [Installing Helm | Helm](https://helm.sh/ru/docs/intro/install/)
7. [Как настроить Helm и K3s кластер на VPS для микросервисов](https://cloudvps.by/community/kak-nastroit-helm-k3s-klaster-na-vps-dlya-mikro%E2%80%91servisov/?ysclid=mo8bfueb75118422641)
8. [Создание Helm-чарта](https://timeweb.cloud/docs/k8s/helm-chart-creation?ysclid=mo8e9iud1n730800580)
9. [Как развернуть приложение с помощью Helm в Kubernetes](https://selectel.ru/blog/tutorials/helm-charts-kubernetes/?ysclid=mo8e9lhndd747894795)
10. [Типы сервисов в Kubernetes и их отличия](https://timeweb.cloud/tutorials/kubernetes/tipy-servisov-kubernetes-kak-vybrat?ysclid=moci5ydzy0145142682#nodeport)
11. [Taints and Tolerations | Kubernetes](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)