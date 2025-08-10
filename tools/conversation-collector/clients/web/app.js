class AgentConversationMonitor {
    constructor() {
        this.apiUrl = 'http://localhost:8005';
        this.wsUrl = 'ws://localhost:8005';
        this.messages = [];
        this.filteredMessages = [];
        this.agents = new Map();
        this.workflows = new Set();
        this.isConnected = false;
        this.websocket = null;
        this.agentColorIndex = 0;
        
        // View mode state
        this.viewMode = 'live'; // 'live' or 'history'
        this.currentPage = 0;
        this.messagesPerPage = 50;
        this.hasMoreMessages = false;
        this.isLoading = false;
        
        // Filter state
        this.filters = {
            timeRange: '1d',
            customDateFrom: null,
            customDateTo: null,
            workflow: '',
            agent: '',
            messageType: '',
            contentSearch: ''
        };
        
        // Agent color mapping
        this.agentColors = new Map();
        this.colorClasses = ['agent-1', 'agent-2', 'agent-3', 'agent-4', 
                           'agent-5', 'agent-6', 'agent-7', 'agent-8'];
        
        // Orchestrator emojis
        this.orchestratorEmojis = {
            'RandomOrchestrator': '🎲',
            'RoundRobinOrchestrator': '🔄', 
            'LLMOrchestrator': '🧠'
        };
        
        // Generic agent emojis
        this.agentEmojis = ['🤖', '🔧', '⚡', '🔮', '🚀', '💎', '🎯', '⭐'];
        
        // Settings
        this.settings = {
            showTimestamps: true,
            showAgentRoles: true,
            maxMessages: 100,
            autoScroll: true,
            hideRoutineMessages: true,
            collapseRoutineMessages: true,
            groupByWorkflow: true
        };
        
        // Store workflow summaries for grouping
        this.workflowSummaries = new Map();
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadSettings();
        this.updateViewModeUI(); // Initialize UI state
        this.connectToAPI();
        this.connectWebSocket();
    }
    
    setupEventListeners() {
        // View mode tabs
        document.getElementById('liveViewBtn').addEventListener('click', () => {
            this.switchToLiveMode();
        });
        
        document.getElementById('historyViewBtn').addEventListener('click', () => {
            this.switchToHistoryMode();
        });
        
        // Auto-scroll toggle (both locations)
        document.getElementById('autoScrollCheckbox').addEventListener('change', (e) => {
            this.settings.autoScroll = e.target.checked;
            this.saveSettings();
        });
        
        document.getElementById('autoScrollCheckboxMain').addEventListener('change', (e) => {
            this.settings.autoScroll = e.target.checked;
            this.saveSettings();
            // Sync with settings panel checkbox
            document.getElementById('autoScrollCheckbox').checked = e.target.checked;
        });
        
        // Clear messages
        document.getElementById('clearButton').addEventListener('click', () => {
            this.clearMessages();
        });
        
        // Export conversations
        document.getElementById('exportButton').addEventListener('click', () => {
            this.exportConversations();
        });
        
        // Refresh button
        document.getElementById('refreshButton').addEventListener('click', () => {
            this.refreshData();
        });
        
        // Load more button
        document.getElementById('loadMoreButton').addEventListener('click', () => {
            this.loadMoreMessages();
        });
        
        // Expand/Collapse all buttons
        document.getElementById('expandAllBtn').addEventListener('click', () => {
            this.expandAllMessages();
        });
        
        document.getElementById('collapseAllBtn').addEventListener('click', () => {
            this.collapseAllMessages();
        });
        
        // History filters
        document.getElementById('timeRangeFilter').addEventListener('change', (e) => {
            this.filters.timeRange = e.target.value;
            this.toggleCustomDateRange();
            if (e.target.value !== 'custom') {
                this.applyFilters();
            }
        });
        
        document.getElementById('applyDateRange').addEventListener('click', () => {
            this.applyCustomDateRange();
        });
        
        document.getElementById('workflowFilter').addEventListener('change', (e) => {
            this.filters.workflow = e.target.value;
            this.applyFilters();
        });
        
        document.getElementById('agentFilter').addEventListener('change', (e) => {
            this.filters.agent = e.target.value;
            this.applyFilters();
        });
        
        document.getElementById('messageTypeFilter').addEventListener('change', (e) => {
            this.filters.messageType = e.target.value;
            this.applyFilters();
        });
        
        document.getElementById('contentSearch').addEventListener('input', (e) => {
            this.filters.contentSearch = e.target.value;
            this.debounceSearch();
        });
        
        // Settings
        document.getElementById('showTimestamps').addEventListener('change', (e) => {
            this.settings.showTimestamps = e.target.checked;
            this.saveSettings();
            this.renderMessages();
        });
        
        document.getElementById('showAgentRoles').addEventListener('change', (e) => {
            this.settings.showAgentRoles = e.target.checked;
            this.saveSettings();
            this.renderMessages();
        });
        
        document.getElementById('messagesPerPage').addEventListener('change', (e) => {
            this.messagesPerPage = parseInt(e.target.value);
            this.applyFilters();
        });
        
        document.getElementById('hideRoutineMessages').addEventListener('change', (e) => {
            this.settings.hideRoutineMessages = e.target.checked;
            this.saveSettings();
            this.applyFilters();
        });
        
        document.getElementById('collapseRoutineMessages').addEventListener('change', (e) => {
            this.settings.collapseRoutineMessages = e.target.checked;
            this.saveSettings();
            this.renderMessages(); // Re-render to apply collapse state
        });
        
        document.getElementById('groupByWorkflow').addEventListener('change', (e) => {
            this.settings.groupByWorkflow = e.target.checked;
            this.saveSettings();
            this.renderMessages(); // Re-render to apply grouping
        });
        
        // Legacy max messages setting (keep for live mode)
        const maxMessagesEl = document.getElementById('maxMessages');
        if (maxMessagesEl) {
            maxMessagesEl.addEventListener('change', (e) => {
                this.settings.maxMessages = parseInt(e.target.value);
                this.saveSettings();
                this.trimMessages();
                this.renderMessages();
            });
        }
    }
    
    loadSettings() {
        const saved = localStorage.getItem('conversationMonitorSettings');
        if (saved) {
            this.settings = { ...this.settings, ...JSON.parse(saved) };
            this.applySettings();
        }
    }
    
    saveSettings() {
        localStorage.setItem('conversationMonitorSettings', JSON.stringify(this.settings));
    }
    
    applySettings() {
        document.getElementById('autoScrollCheckbox').checked = this.settings.autoScroll;
        document.getElementById('autoScrollCheckboxMain').checked = this.settings.autoScroll;
        document.getElementById('showTimestamps').checked = this.settings.showTimestamps;
        document.getElementById('showAgentRoles').checked = this.settings.showAgentRoles;
        document.getElementById('hideRoutineMessages').checked = this.settings.hideRoutineMessages;
        document.getElementById('collapseRoutineMessages').checked = this.settings.collapseRoutineMessages;
        document.getElementById('groupByWorkflow').checked = this.settings.groupByWorkflow;
        document.getElementById('messagesPerPage').value = this.messagesPerPage;
        
        const maxMessagesEl = document.getElementById('maxMessages');
        if (maxMessagesEl) {
            maxMessagesEl.value = this.settings.maxMessages;
        }
    }
    
    // View Mode Management
    switchToLiveMode() {
        this.viewMode = 'live';
        this.updateViewModeUI();
        this.connectWebSocket(); // Reconnect if needed
        this.loadInitialMessages();
    }
    
    switchToHistoryMode() {
        this.viewMode = 'history';
        this.updateViewModeUI();
        this.loadHistoryMessages();
    }
    
    updateViewModeUI() {
        const liveBtn = document.getElementById('liveViewBtn');
        const historyBtn = document.getElementById('historyViewBtn');
        const filtersPanel = document.getElementById('historyFiltersPanel');
        const loadMoreSection = document.getElementById('loadMoreSection');
        const autoScrollSetting = document.getElementById('autoScrollSetting');
        const panelHeader = document.querySelector('.panel-header h2');
        
        if (this.viewMode === 'live') {
            liveBtn.classList.add('active');
            historyBtn.classList.remove('active');
            filtersPanel.style.display = 'none';
            loadMoreSection.style.display = 'none';
            autoScrollSetting.style.display = 'block';
            panelHeader.textContent = '💬 Live Conversations';
        } else {
            liveBtn.classList.remove('active');
            historyBtn.classList.add('active');
            filtersPanel.style.display = 'block';
            loadMoreSection.style.display = 'block';
            autoScrollSetting.style.display = 'none';
            panelHeader.textContent = '📚 Conversation History';
        }
    }
    
    // Filter Management
    toggleCustomDateRange() {
        const customRange = document.getElementById('customDateRange');
        if (this.filters.timeRange === 'custom') {
            customRange.style.display = 'block';
        } else {
            customRange.style.display = 'none';
        }
    }
    
    applyCustomDateRange() {
        const fromDate = document.getElementById('dateFrom').value;
        const toDate = document.getElementById('dateTo').value;
        
        if (fromDate && toDate) {
            this.filters.customDateFrom = new Date(fromDate);
            this.filters.customDateTo = new Date(toDate);
            this.applyFilters();
        } else {
            alert('Please select both start and end dates');
        }
    }
    
    debounceSearch() {
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        this.searchTimeout = setTimeout(() => {
            this.applyFilters();
        }, 300);
    }
    
    applyFilters() {
        if (this.viewMode === 'live') {
            // In live mode, just filter the current messages
            this.filterCurrentMessages();
        } else {
            // In history mode, reload with filters
            this.currentPage = 0;
            this.loadHistoryMessages();
        }
    }
    
    filterCurrentMessages() {
        this.filteredMessages = this.messages.filter(message => {
            return this.messagePassesFilter(message);
        });
        this.renderMessages();
    }
    
    isRoutineMessage(message) {
        const content = (message.content || '').trim().toLowerCase();
        
        // Define patterns for routine/protocol messages based on actual ConversationCollector output
        const routinePatterns = [
            /^agent message$/, // Default fallback from parser
            /^orchestrator action$/, // Default fallback from parser
            /^workflow started$/, // Workflow lifecycle
            /^workflow completed$/, // Workflow lifecycle
            /^request$/, // Simple protocol messages
            /^response$/, // Simple protocol messages
            /^ack$/, // Acknowledgment
            /^ping$/, // Ping messages
            /^pong$/, // Pong messages
            /^ok$/, // Simple OK responses
            /^ready$/, // Ready status
            /^start$/, // Start signals
            /^end$/, // End signals
        ];
        
        // Check if message is very short (likely protocol noise)
        if (content.length <= 3) {
            return true;
        }
        
        // Check against routine patterns
        return routinePatterns.some(pattern => pattern.test(content));
    }
    
    messagePassesFilter(message) {
        // Hide routine messages setting
        if (this.settings.hideRoutineMessages && this.isRoutineMessage(message)) {
            return false;
        }
        
        // Time range filter
        if (this.filters.timeRange !== 'all' && this.filters.timeRange !== 'custom') {
            const messageTime = new Date(message.timestamp);
            const now = new Date();
            const cutoff = new Date();
            
            switch (this.filters.timeRange) {
                case '1h':
                    cutoff.setHours(now.getHours() - 1);
                    break;
                case '6h':
                    cutoff.setHours(now.getHours() - 6);
                    break;
                case '1d':
                    cutoff.setDate(now.getDate() - 1);
                    break;
                case '3d':
                    cutoff.setDate(now.getDate() - 3);
                    break;
                case '1w':
                    cutoff.setDate(now.getDate() - 7);
                    break;
            }
            
            if (messageTime < cutoff) return false;
        }
        
        // Custom date range filter
        if (this.filters.timeRange === 'custom' && this.filters.customDateFrom && this.filters.customDateTo) {
            const messageTime = new Date(message.timestamp);
            if (messageTime < this.filters.customDateFrom || messageTime > this.filters.customDateTo) {
                return false;
            }
        }
        
        // Workflow filter
        if (this.filters.workflow && message.workflow_id !== this.filters.workflow) {
            return false;
        }
        
        // Agent filter
        if (this.filters.agent && message.agent_name !== this.filters.agent) {
            return false;
        }
        
        // Message type filter
        if (this.filters.messageType && message.message_type !== this.filters.messageType) {
            return false;
        }
        
        // Content search filter
        if (this.filters.contentSearch) {
            const searchTerm = this.filters.contentSearch.toLowerCase();
            const content = (message.content || '').toLowerCase();
            const agentName = (message.agent_name || '').toLowerCase();
            
            if (!content.includes(searchTerm) && !agentName.includes(searchTerm)) {
                return false;
            }
        }
        
        return true;
    }
    
    async connectToAPI() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            if (response.ok) {
                this.updateConnectionStatus('connected');
                await this.loadInitialMessages();
            } else {
                throw new Error('API health check failed');
            }
        } catch (error) {
            console.error('Failed to connect to API:', error);
            this.updateConnectionStatus('disconnected');
            // Retry after 5 seconds
            setTimeout(() => this.connectToAPI(), 5000);
        }
    }
    
    async loadInitialMessages() {
        try {
            const response = await fetch(`${this.apiUrl}/conversations/latest?limit=50`);
            if (response.ok) {
                const data = await response.json();
                this.messages = data.messages || [];
                this.messages.reverse(); // Show oldest first
                
                // Load workflow summaries for grouping
                await this.loadWorkflowSummaries();
                
                if (this.viewMode === 'live') {
                    this.renderMessages();
                } else {
                    this.filterCurrentMessages();
                }
                this.updateStatistics();
                this.updateFilterDropdowns();
                this.hideLoading();
            }
        } catch (error) {
            console.error('Failed to load initial messages:', error);
        }
    }
    
    async loadWorkflowSummaries() {
        try {
            const response = await fetch(`${this.apiUrl}/conversations/summaries`);
            if (response.ok) {
                const summaries = await response.json();
                this.workflowSummaries.clear();
                summaries.forEach(summary => {
                    this.workflowSummaries.set(summary.workflow_id, summary);
                });
            }
        } catch (error) {
            console.error('Failed to load workflow summaries:', error);
        }
    }
    
    async loadHistoryMessages() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            // Build query parameters
            const params = new URLSearchParams({
                page: this.currentPage.toString(),
                limit: this.messagesPerPage.toString()
            });
            
            // Add time range filter
            if (this.filters.timeRange !== 'all') {
                if (this.filters.timeRange === 'custom' && this.filters.customDateFrom && this.filters.customDateTo) {
                    params.append('start_time', this.filters.customDateFrom.toISOString());
                    params.append('end_time', this.filters.customDateTo.toISOString());
                } else {
                    // Calculate time range
                    const now = new Date();
                    const startTime = new Date();
                    
                    switch (this.filters.timeRange) {
                        case '1h':
                            startTime.setHours(now.getHours() - 1);
                            break;
                        case '6h':
                            startTime.setHours(now.getHours() - 6);
                            break;
                        case '1d':
                            startTime.setDate(now.getDate() - 1);
                            break;
                        case '3d':
                            startTime.setDate(now.getDate() - 3);
                            break;
                        case '1w':
                            startTime.setDate(now.getDate() - 7);
                            break;
                    }
                    
                    params.append('start_time', startTime.toISOString());
                }
            }
            
            // Add other filters
            if (this.filters.workflow) {
                params.append('workflow_id', this.filters.workflow);
            }
            if (this.filters.agent) {
                params.append('agent_name', this.filters.agent);
            }
            if (this.filters.messageType) {
                params.append('message_type', this.filters.messageType);
            }
            if (this.filters.contentSearch) {
                params.append('search', this.filters.contentSearch);
            }
            
            const response = await fetch(`${this.apiUrl}/conversations/history?${params}`);
            if (response.ok) {
                const data = await response.json();
                
                if (this.currentPage === 0) {
                    // First page - replace messages
                    this.messages = data.messages || [];
                } else {
                    // Additional pages - append messages
                    this.messages.push(...(data.messages || []));
                }
                
                this.hasMoreMessages = data.has_more || false;
                this.filteredMessages = this.messages;
                
                // Load workflow summaries for grouping
                await this.loadWorkflowSummaries();
                
                this.renderMessages();
                this.updateStatistics();
                this.updateFilterDropdowns();
                this.updatePagination();
            }
        } catch (error) {
            console.error('Failed to load history messages:', error);
        } finally {
            this.isLoading = false;
            this.hideLoading();
        }
    }
    
    async loadMoreMessages() {
        if (this.hasMoreMessages && !this.isLoading) {
            this.currentPage++;
            await this.loadHistoryMessages();
        }
    }
    
    async refreshData() {
        if (this.viewMode === 'live') {
            await this.loadInitialMessages();
        } else {
            this.currentPage = 0;
            await this.loadHistoryMessages();
        }
    }
    
    updateFilterDropdowns() {
        // Update workflow dropdown
        const workflowFilter = document.getElementById('workflowFilter');
        const currentWorkflow = workflowFilter.value;
        workflowFilter.innerHTML = '<option value="">All Workflows</option>';
        
        const workflows = Array.from(new Set(
            this.messages.map(m => m.workflow_id).filter(Boolean)
        )).sort();
        
        workflows.forEach(workflow => {
            const option = document.createElement('option');
            option.value = workflow;
            option.textContent = workflow;
            workflowFilter.appendChild(option);
        });
        
        if (workflows.includes(currentWorkflow)) {
            workflowFilter.value = currentWorkflow;
        }
        
        // Update agent dropdown
        const agentFilter = document.getElementById('agentFilter');
        const currentAgent = agentFilter.value;
        agentFilter.innerHTML = '<option value="">All Agents</option>';
        
        const agents = Array.from(new Set(
            this.messages.map(m => m.agent_name).filter(Boolean)
        )).sort();
        
        agents.forEach(agent => {
            const option = document.createElement('option');
            option.value = agent;
            option.textContent = agent;
            agentFilter.appendChild(option);
        });
        
        if (agents.includes(currentAgent)) {
            agentFilter.value = currentAgent;
        }
    }
    
    updatePagination() {
        const paginationInfo = document.getElementById('paginationInfo');
        const loadMoreSection = document.getElementById('loadMoreSection');
        const loadMoreButton = document.getElementById('loadMoreButton');
        const loadStatus = document.getElementById('loadStatus');
        
        if (this.viewMode === 'history') {
            const totalShown = this.messages.length;
            paginationInfo.textContent = `Showing ${totalShown} messages`;
            
            if (this.hasMoreMessages) {
                loadMoreButton.style.display = 'block';
                loadMoreButton.disabled = this.isLoading;
                loadStatus.textContent = this.isLoading ? 'Loading...' : '';
            } else {
                loadMoreButton.style.display = 'none';
                loadStatus.textContent = totalShown > 0 ? 'All messages loaded' : '';
            }
        } else {
            paginationInfo.textContent = '';
            loadMoreSection.style.display = 'none';
        }
    }
    
    connectWebSocket() {
        try {
            this.websocket = new WebSocket(`${this.wsUrl}/conversations/live`);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus('connected');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'new_message' && data.message) {
                        this.addMessage(data.message);
                    } else if (data.type === 'initial_messages') {
                        this.messages = data.messages.slice(-50);
                        this.messages.reverse();
                        this.renderMessages();
                        this.updateStatistics();
                    }
                } catch (error) {
                    console.error('Error processing WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus('connecting');
                // Reconnect after 5 seconds
                setTimeout(() => this.connectWebSocket(), 5000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('disconnected');
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.updateConnectionStatus('disconnected');
            setTimeout(() => this.connectWebSocket(), 5000);
        }
    }
    
    updateConnectionStatus(status) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        
        statusDot.className = `status-dot ${status}`;
        
        switch (status) {
            case 'connected':
                statusText.textContent = 'Connected';
                this.isConnected = true;
                break;
            case 'connecting':
                statusText.textContent = 'Connecting...';
                this.isConnected = false;
                break;
            case 'disconnected':
                statusText.textContent = 'Disconnected';
                this.isConnected = false;
                break;
        }
    }
    
    getAgentColor(agentName) {
        if (!this.agentColors.has(agentName)) {
            const colorClass = this.colorClasses[this.agentColorIndex % this.colorClasses.length];
            this.agentColors.set(agentName, colorClass);
            this.agentColorIndex++;
        }
        return this.agentColors.get(agentName);
    }
    
    getAgentEmoji(agentName) {
        // Check if it's an orchestrator
        if (this.orchestratorEmojis[agentName]) {
            return this.orchestratorEmojis[agentName];
        }
        
        // Use a consistent emoji based on agent name hash
        let hash = 0;
        for (let i = 0; i < agentName.length; i++) {
            hash = ((hash << 5) - hash + agentName.charCodeAt(i)) & 0xffffffff;
        }
        const index = Math.abs(hash) % this.agentEmojis.length;
        return this.agentEmojis[index];
    }
    
    formatTimestamp(timestampStr) {
        try {
            const date = new Date(timestampStr);
            return date.toLocaleTimeString('en-US', { 
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } catch {
            return '??:??:??';
        }
    }
    
    getMessageTypeDisplay(messageType) {
        const typeMap = {
            'agent_request': '📤 Request',
            'agent_response': '💬 Response',
            'orchestrator_action': '⚡ Action',
            'workflow_start': '🚀 Start',
            'workflow_end': '🏁 End'
        };
        return typeMap[messageType] || messageType;
    }
    
    addMessage(message) {
        // Only add to live messages in live mode
        if (this.viewMode === 'live') {
            this.messages.push(message);
            this.trimMessages();
            
            // Track agents and workflows
            if (message.agent_name) {
                const count = this.agents.get(message.agent_name) || 0;
                this.agents.set(message.agent_name, count + 1);
            }
            
            if (message.workflow_id) {
                this.workflows.add(message.workflow_id);
            }
            
            // Check if message passes current filters
            if (this.messagePassesFilter(message)) {
                this.renderNewMessage(message);
            }
            
            this.updateStatistics();
            this.updateFilterDropdowns();
            
            if (this.settings.autoScroll) {
                this.scrollToBottom();
            }
        }
    }
    
    trimMessages() {
        if (this.messages.length > this.settings.maxMessages) {
            this.messages = this.messages.slice(-this.settings.maxMessages);
        }
    }
    
    renderNewMessage(message) {
        const messageElement = this.createMessageElement(message);
        messageElement.classList.add('message-enter');
        
        const container = document.getElementById('messagesContainer');
        container.appendChild(messageElement);
        
        this.updateMessageCount();
    }
    
    renderMessages() {
        const container = document.getElementById('messagesContainer');
        container.innerHTML = '';
        
        const messagesToRender = this.viewMode === 'history' ? 
            this.filteredMessages : 
            (this.filteredMessages.length > 0 ? this.filteredMessages : this.messages);
        
        if (messagesToRender.length === 0) {
            this.showEmptyState();
            return;
        }
        
        if (this.settings.groupByWorkflow) {
            this.renderGroupedByWorkflow(messagesToRender, container);
        } else {
            this.renderFlatMessages(messagesToRender, container);
        }
        
        this.updateMessageCount();
        this.updatePagination();
    }
    
    renderGroupedByWorkflow(messages, container) {
        // Group messages by workflow_id
        const workflowGroups = new Map();
        
        messages.forEach(message => {
            const workflowId = message.workflow_id || 'unknown';
            if (!workflowGroups.has(workflowId)) {
                workflowGroups.set(workflowId, []);
            }
            workflowGroups.get(workflowId).push(message);
        });
        
        // Sort workflows by most recent message timestamp
        const sortedWorkflows = Array.from(workflowGroups.entries()).sort((a, b) => {
            const aLatestTime = Math.max(...a[1].map(m => new Date(m.timestamp).getTime()));
            const bLatestTime = Math.max(...b[1].map(m => new Date(m.timestamp).getTime()));
            return bLatestTime - aLatestTime; // Most recent first
        });
        
        // Create workflow sections
        sortedWorkflows.forEach(([workflowId, workflowMessages]) => {
            // Sort messages within workflow by timestamp
            workflowMessages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            
            const workflowSection = this.createWorkflowSection(workflowId, workflowMessages);
            container.appendChild(workflowSection);
        });
    }
    
    renderFlatMessages(messages, container) {
        messages.forEach(message => {
            const messageElement = this.createMessageElement(message);
            container.appendChild(messageElement);
        });
    }
    
    createWorkflowSection(workflowId, messages) {
        const template = document.getElementById('workflowTemplate');
        const element = template.content.cloneNode(true);
        const workflowDiv = element.querySelector('.workflow-section');
        
        workflowDiv.dataset.workflow = workflowId;
        
        // Get workflow summary data
        const summary = this.workflowSummaries.get(workflowId) || {
            workflow_id: workflowId,
            agent_names: [...new Set(messages.map(m => m.agent_name).filter(Boolean))],
            message_count: messages.length,
            status: 'unknown'
        };
        
        // Determine if this workflow should be collapsed by default
        // Active workflows expanded, completed ones collapsed
        const shouldCollapse = summary.status === 'completed' || messages.length < 5;
        if (shouldCollapse) {
            workflowDiv.classList.add('collapsed');
        }
        
        // Add click handler for workflow expand/collapse
        const header = element.querySelector('.workflow-header');
        header.addEventListener('click', () => {
            workflowDiv.classList.toggle('collapsed');
        });
        
        // Handle keyboard navigation
        header.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                workflowDiv.classList.toggle('collapsed');
            }
        });
        
        // Fill in workflow data
        element.querySelector('.workflow-id').textContent = this.formatWorkflowId(workflowId);
        
        // Create metadata string
        const agentCount = summary.agent_names.length;
        const messageCount = summary.message_count;
        const metadata = `${agentCount} agent${agentCount !== 1 ? 's' : ''}, ${messageCount} message${messageCount !== 1 ? 's' : ''}`;
        element.querySelector('.workflow-metadata').textContent = metadata;
        
        // Set status
        const statusElement = element.querySelector('.workflow-status');
        statusElement.textContent = summary.status || 'active';
        statusElement.classList.add(summary.status || 'active');
        
        // Set timestamp (use first message timestamp)
        const firstMessage = messages[0];
        if (firstMessage && firstMessage.timestamp) {
            element.querySelector('.workflow-timestamp').textContent = this.formatWorkflowTimestamp(firstMessage.timestamp);
        }
        
        // Add messages to the workflow section
        const messagesContainer = element.querySelector('.workflow-messages');
        messages.forEach(message => {
            const messageElement = this.createMessageElement(message);
            messagesContainer.appendChild(messageElement);
        });
        
        return workflowDiv;
    }
    
    formatWorkflowId(workflowId) {
        // Convert "workflow_20250810_174920" to "Session 17:49:20"
        const match = workflowId.match(/workflow_(\d{8})_(\d{6})/);
        if (match) {
            const timeStr = match[2];
            const hours = timeStr.substring(0, 2);
            const minutes = timeStr.substring(2, 4);
            const seconds = timeStr.substring(4, 6);
            return `Session ${hours}:${minutes}:${seconds}`;
        }
        return workflowId;
    }
    
    formatWorkflowTimestamp(timestampStr) {
        try {
            const date = new Date(timestampStr);
            return date.toLocaleTimeString('en-US', { 
                hour12: false,
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return '??:??';
        }
    }
    
    createMessageElement(message) {
        const template = document.getElementById('messageTemplate');
        const element = template.content.cloneNode(true);
        const messageDiv = element.querySelector('.message');
        
        const agentName = message.agent_name || 'Unknown';
        const colorClass = this.getAgentColor(agentName);
        const emoji = this.getAgentEmoji(agentName);
        
        // Apply agent color class
        messageDiv.classList.add(colorClass);
        messageDiv.dataset.agent = agentName;
        messageDiv.dataset.workflow = message.workflow_id || '';
        
        // Check if this is a routine message and collapse it by default
        const isRoutine = this.isRoutineMessage(message);
        if (isRoutine && this.settings.collapseRoutineMessages) {
            messageDiv.classList.add('collapsed');
        }
        
        // Add click handler for expand/collapse
        const header = element.querySelector('.message-header');
        header.addEventListener('click', () => {
            messageDiv.classList.toggle('collapsed');
        });
        
        // Handle keyboard navigation
        header.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                messageDiv.classList.toggle('collapsed');
            }
        });
        
        // Fill in message data
        element.querySelector('.agent-emoji').textContent = emoji;
        element.querySelector('.agent-name').textContent = agentName;
        
        // Agent role
        const roleElement = element.querySelector('.agent-role');
        if (this.settings.showAgentRoles && message.agent_role && message.agent_role !== 'user') {
            roleElement.textContent = `(${message.agent_role})`;
        } else {
            roleElement.style.display = 'none';
        }
        
        // Turn number
        const turnElement = element.querySelector('.turn-number');
        if (message.turn_number && message.turn_number > 0) {
            turnElement.textContent = `#${message.turn_number}`;
        } else {
            turnElement.style.display = 'none';
        }
        
        // Message type
        const typeElement = element.querySelector('.message-type');
        if (message.message_type) {
            typeElement.textContent = this.getMessageTypeDisplay(message.message_type);
        } else {
            typeElement.style.display = 'none';
        }
        
        // Timestamp
        const timestampElement = element.querySelector('.timestamp');
        if (this.settings.showTimestamps && message.timestamp) {
            timestampElement.textContent = this.formatTimestamp(message.timestamp);
        } else {
            timestampElement.style.display = 'none';
        }
        
        // Message content
        const contentElement = element.querySelector('.message-content');
        const content = message.content || '';
        if (content.length > 1000) {
            contentElement.textContent = content.substring(0, 1000) + '...';
        } else if (content) {
            contentElement.textContent = content;
        } else {
            contentElement.innerHTML = '<em style="color: var(--text-muted);">No content</em>';
        }
        
        return messageDiv;
    }
    
    showEmptyState() {
        const container = document.getElementById('messagesContainer');
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-emoji">🔍</div>
                <div class="empty-state-text">No conversations yet</div>
                <div class="empty-state-subtext">Start an agent workflow to see messages here!</div>
            </div>
        `;
    }
    
    hideLoading() {
        const loading = document.getElementById('loadingMessage');
        if (loading) {
            loading.style.display = 'none';
        }
    }
    
    updateMessageCount() {
        const totalMessages = this.viewMode === 'history' ? 
            this.filteredMessages.length : 
            (this.filteredMessages.length > 0 ? this.filteredMessages.length : this.messages.length);
            
        document.getElementById('messageCount').textContent = 
            `${totalMessages} message${totalMessages !== 1 ? 's' : ''}`;
    }
    
    updateStatistics() {
        // Count agents and their messages
        const agentCounts = new Map();
        const workflowIds = new Set();
        
        this.messages.forEach(message => {
            if (message.agent_name) {
                const count = agentCounts.get(message.agent_name) || 0;
                agentCounts.set(message.agent_name, count + 1);
            }
            if (message.workflow_id) {
                workflowIds.add(message.workflow_id);
            }
        });
        
        // Update stats
        document.getElementById('totalMessages').textContent = this.messages.length;
        document.getElementById('activeWorkflows').textContent = workflowIds.size;
        document.getElementById('activeAgents').textContent = agentCounts.size;
        
        // Update agent list
        this.updateAgentList(agentCounts);
    }
    
    updateAgentList(agentCounts) {
        const agentList = document.getElementById('agentList');
        agentList.innerHTML = '';
        
        // Sort agents by message count
        const sortedAgents = Array.from(agentCounts.entries())
            .sort((a, b) => b[1] - a[1]);
        
        sortedAgents.forEach(([agentName, count]) => {
            const item = document.createElement('div');
            item.className = 'agent-item';
            
            const emoji = this.getAgentEmoji(agentName);
            const colorClass = this.getAgentColor(agentName);
            
            item.innerHTML = `
                <div class="agent-item-name">
                    <span>${emoji}</span>
                    <span class="${colorClass}">${agentName}</span>
                </div>
                <span class="agent-item-count">${count}</span>
            `;
            
            agentList.appendChild(item);
        });
    }
    
    showLoading() {
        const loading = document.getElementById('loadingMessage');
        if (loading) {
            loading.style.display = 'flex';
        }
    }
    
    clearMessages() {
        if (confirm('Are you sure you want to clear all messages?')) {
            this.messages = [];
            this.filteredMessages = [];
            this.agents.clear();
            this.workflows.clear();
            this.renderMessages();
            this.updateStatistics();
            this.updateFilterDropdowns();
        }
    }
    
    exportConversations() {
        if (this.messages.length === 0) {
            alert('No conversations to export');
            return;
        }
        
        const data = {
            exportDate: new Date().toISOString(),
            totalMessages: this.messages.length,
            conversations: this.messages
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `agent-conversations-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    scrollToBottom() {
        const container = document.getElementById('messagesContainer');
        container.scrollTop = container.scrollHeight;
    }
    
    expandAllMessages() {
        const messages = document.querySelectorAll('.message.collapsed');
        messages.forEach(message => {
            message.classList.remove('collapsed');
        });
    }
    
    collapseAllMessages() {
        const messages = document.querySelectorAll('.message:not(.collapsed)');
        messages.forEach(message => {
            message.classList.add('collapsed');
        });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AgentConversationMonitor();
});