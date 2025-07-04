// 創建日誌容器
function createLogContainer() {
    const logContainer = document.createElement('div');
    logContainer.style.position = 'fixed';
    logContainer.style.bottom = '0';
    logContainer.style.right = '0';
    logContainer.style.width = '300px';
    logContainer.style.maxHeight = '200px';
    logContainer.style.backgroundColor = 'rgba(0,0,0,0.7)';
    logContainer.style.color = 'white';
    logContainer.style.padding = '10px';
    logContainer.style.fontFamily = 'monospace';
    logContainer.style.fontSize = '12px';
    logContainer.style.zIndex = '10000';
    logContainer.style.overflow = 'auto';
    logContainer.style.borderTopLeftRadius = '5px';
    logContainer.id = 'playwright-recorder-log';
    
    // 添加標題
    const title = document.createElement('div');
    title.textContent = 'Playwright 錄製中';
    title.style.fontWeight = 'bold';
    title.style.borderBottom = '1px solid white';
    title.style.marginBottom = '5px';
    title.style.paddingBottom = '5px';
    logContainer.appendChild(title);
    
    document.body.appendChild(logContainer);
    
    // 記錄函數
    window._playwrightLog = function(message) {
        const log = document.createElement('div');
        log.textContent = message;
        log.style.borderBottom = '1px dotted #555';
        log.style.paddingBottom = '3px';
        log.style.marginBottom = '3px';
        
        const container = document.getElementById('playwright-recorder-log');
        if (container) {
            container.appendChild(log);
            container.scrollTop = container.scrollHeight;
            
            // 只保留最近的10條日誌
            const logs = container.querySelectorAll('div:not(:first-child)');
            if (logs.length > 10) {
                container.removeChild(logs[0]);
            }
        }
    };
}

// 設置事件監聽器
function setupEventListeners() {
    // 監聽點擊事件
    window.addEventListener('click', (event) => {
        const target = event.target;
        // 記錄點擊
        window._playwrightLog(`點擊: ${target.tagName} ${target.id ? '#'+target.id : ''}`);
        console.log(`RECORDER_CLICK:${JSON.stringify({
            x: event.clientX, 
            y: event.clientY,
            tagName: target.tagName,
            id: target.id,
            className: target.className,
            textContent: target.textContent ? target.textContent.slice(0, 50) : ''
        })}`);
    }, true);
    
    // 監聽輸入事件
    document.addEventListener('input', (event) => {
        const target = event.target;
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
            window._playwrightLog(`輸入: ${target.tagName} ${target.id ? '#'+target.id : ''}`);
            console.log(`RECORDER_FILL:${JSON.stringify({
                tagName: target.tagName,
                id: target.id,
                name: target.name,
                value: target.value,
                type: target.type
            })}`);
        }
    }, true);
    
    // 監聽選擇事件
    document.addEventListener('change', (event) => {
        const target = event.target;
        if (target.tagName === 'SELECT') {
            const selectedText = Array.from(target.selectedOptions)
                .map(option => option.text)
                .join(', ');
            window._playwrightLog(`選擇: ${target.tagName} ${target.id ? '#'+target.id : ''}`);
            console.log(`RECORDER_SELECT:${JSON.stringify({
                tagName: target.tagName,
                id: target.id,
                name: target.name,
                value: target.value,
                selectedIndex: target.selectedIndex,
                selectedText: selectedText
            })}`);
        }
    }, true);
}

// 初始化錄製
function initRecorder() {
    createLogContainer();
    setupEventListeners();
    console.log("RECORDER_INITIALIZED");
}

// 執行初始化
initRecorder(); 