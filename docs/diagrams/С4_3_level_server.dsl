workspace  {

    model {
        user = person "Пользователь"

        system = softwareSystem  "Система обработки PDF" {
            bot = container "Telegram Bot" "Один из возможных интерфейсов взаимодествия" "Node.js, grammY" 
            server = container  "Server" "Доступ только для доверенных клинтов" {
                nginx = component "Nginx" "Обратный прокси, сертификат" "Nginx"
                api = component "API" "Обработка ошибок, работа с очередью, приняте запросов клиента" "FastAPI"
                queue = component "Queue" "Хранит задачи для ML сервиса" "RabbitMQ"
                redis = component "Redis" "Временное хранилище статусов задач (job_id → status/error/temp_path_file/result)" "Redis"
                ml = component "ML Service" "Распознование текста, выявление структуры, отпрака ответа (формально это request на api)"
                dir = component "Shared temporary volume" "Очищаемый volume для передачи файлов" "Docker volume"
            }
        }
        
        user -> system "Отправляет PDF"
        system -> user "Возвращает результат обработки"

        user -> bot "Отправляет PDF"
        
        bot -> nginx "HTTPS multipart/formdata"
        bot -> nginx "HTTPS polling, проверяет результат по job_id"
        nginx -> bot "Возвращает job_id для polling`а" 
        nginx -> bot "Возвращает JSON со статусом + JSON struct result"
        
        nginx -> api "Обратный HTTPS прокси"
        api -> queue "job_id, temp_file_path, time ..."
        api -> redis "Кладет job, потом проверяет сатутс, если готов то берет и удаляет"
        api -> dir "Кладет файл в волюм, когда получил результат очищает по temp_file_path"
        ml -> queue "Берет в работу ближайший job"
        ml -> dir "Берет файл"
        ml -> redis "Обновляет result, status, error, temp_file_path (чтобы апи удалил временный файл)"
    }

    views {
        systemContext system {
            include *
            autolayout lr
            title "C4-1 System Context"
        }

        container system {
            include *
            autolayout lr
            title "C4-2 Container View: System"
        }
        
        component server {
            title "C4-3 Component View: Server"
            include *
            autolayout lr
        }
        
        theme default
    }
}
