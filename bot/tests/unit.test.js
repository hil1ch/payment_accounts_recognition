const { handleUploadError } = require('../src/bot.js');

const mockCtx = (replyMock) => ({
    reply: replyMock,
    chat: { id: 123 }
});

describe('handleUploadError Unit Tests', () => {
    let replyMock;
    let ctx;

    beforeEach(() => {
        replyMock = jest.fn();
        ctx = mockCtx(replyMock);
    });

    
    test('1. ECONNABORTED (ML service timeout)', async () => {
        const error = { code: 'ECONNABORTED' };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Превышено времени ожидания ответа от ML сервиса');
    });

    test('2. Unknown error (no response, no known code)', async () => {
        const error = new Error('Some internal error');
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Произошла неизвестная ошибка. Попробуйте позже.');
    });

    test('3. HTTP 400 (Bad Request)', async () => {
        const error = { response: { status: 400 } };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Неверный формат запроса. Убедитесь, что вы отправили PDF-файл.');
    });

    test('4. HTTP 413 (Payload Too Large)', async () => {
        const error = { response: { status: 413 } };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Файл больше 10 МБ. Сожмите или разделите документ.');
    });

    test('5. HTTP 429 (Too Many Requests)', async () => {
        const error = { response: { status: 429 } };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Слишком много запросов. Подождите 1 мин и повторите.');
    });
    
    test('6. HTTP 500 (Internal Server Error)', async () => {
        const error = { response: { status: 500 } };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Ошибка сервера. Мы уже разбираемся, попробуйте позже.');
    });

    test('7. HTTP 502 (Bad Gateway/ML Service Unavailable)', async () => {
        const error = { response: { status: 502 } };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Сервис распознавания временно недоступен. Попробуйте позже.');
    });

    test('8. Other HTTP error (e.g., 504 Gateway Timeout, 503)', async () => {
        const error = { response: { status: 504 } };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Произошла ошибка при обработке файла. Попробуйте позже.');
    });

    test('9. HTTP 408 (Request Timeout from ML service)', async () => {
        const error = { response: { status: 408 } };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Превышено времени ожидания ответа от ML сервиса');
    });

    test('10. HTTP 404 (Result expired or not found)', async () => {
        const error = { response: { status: 404 } };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Результат устарел или не существует. Начните заново.');
    });

    test('11. HTTP 415 (Unsupported Media Type - not PDF)', async () => {
        const error = { response: { status: 415 } };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Принимаются только PDF-файлы.');
    });

    test('12. HTTP 503 (Service Unavailable)', async () => {
        const error = { response: { status: 503 } };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Произошла ошибка при обработке файла. Попробуйте позже.');
    });

    test('13. HTTP 504 (Gateway Timeout)', async () => {
        const error = { response: { status: 504 } };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Произошла ошибка при обработке файла. Попробуйте позже.');
    });

    test('14. Network error without code (ENOTFOUND, ECONNREFUSED)', async () => {
        const error = { 
            code: 'ENOTFOUND',
            message: 'getaddrinfo ENOTFOUND ml-service.local'
        };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Произошла неизвестная ошибка. Попробуйте позже.');
    });

    test('15. Error with message but no code or response', async () => {
        const error = { 
            message: 'Random error occurred',
            stack: 'Error: Random error occurred'
        };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Произошла неизвестная ошибка. Попробуйте позже.');
    });

    test('16. Empty error object', async () => {
        const error = {};
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Произошла неизвестная ошибка. Попробуйте позже.');
    });

    test('17. Verify error message for status 408 from ML service', async () => {
        const error = { response: { status: 408 } };
        await handleUploadError(ctx, error);
        
        expect(replyMock).toHaveBeenCalledWith('✗ Превышено времени ожидания ответа от ML сервиса');
    });

    test('18. Multiple calls to reply method should not happen', async () => {
        const error = { response: { status: 400 } };
        await handleUploadError(ctx, error);
        // Проверяем, что reply вызывается только 1 раз
        expect(replyMock).toHaveBeenCalledTimes(1);
    });

    test('19. Error with nested response structure', async () => {
        const error = { 
            response: { 
                status: 500,
                data: { message: 'Internal error' }
            }
        };
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Ошибка сервера. Мы уже разбираемся, попробуйте позже.');
    });
});

describe('handleUploadError Edge Cases', () => {
    let replyMock;
    let ctx;

    beforeEach(() => {
        replyMock = jest.fn();
        ctx = mockCtx(replyMock);
    });

    test('Should handle string error message', async () => {
        const error = 'Some string error';
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Произошла неизвестная ошибка. Попробуйте позже.');
    });

    test('Should handle number error', async () => {
        const error = 500;
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Произошла неизвестная ошибка. Попробуйте позже.');
    });

    test('Should handle boolean error', async () => {
        const error = true;
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Произошла неизвестная ошибка. Попробуйте позже.');
    });

    test('Should handle array error', async () => {
        const error = ['error1', 'error2'];
        await handleUploadError(ctx, error);
        expect(replyMock).toHaveBeenCalledWith('✗ Произошла неизвестная ошибка. Попробуйте позже.');
    });

    test('Should work when reply method returns promise', async () => {
        replyMock = jest.fn().mockResolvedValue({ message_id: 456 });
        ctx = mockCtx(replyMock);
        
        const error = { response: { status: 400 } };
        await handleUploadError(ctx, error);
        
        expect(replyMock).toHaveBeenCalledTimes(1);
        expect(replyMock).toHaveBeenCalledWith('✗ Неверный формат запроса. Убедитесь, что вы отправили PDF-файл.');
    });
});
