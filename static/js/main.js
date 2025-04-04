document.addEventListener('DOMContentLoaded', function() {
    // Toggle task completion
    document.querySelectorAll('.task-check').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const taskId = this.getAttribute('data-task-id');
            
            fetch(`/task/${taskId}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                const taskItem = document.querySelector(`.task-item[data-task-id="${taskId}"]`);
                
                if (data.completed) {
                    taskItem.classList.add('completed');
                    const statusBadge = taskItem.querySelector('.badge');
                    if (statusBadge) {
                        statusBadge.className = 'badge status-completed';
                        statusBadge.textContent = 'Completed';
                    }
                } else {
                    taskItem.classList.remove('completed');
                    const statusBadge = taskItem.querySelector('.badge');
                    if (statusBadge) {
                        statusBadge.className = 'badge status-pending';
                        statusBadge.textContent = 'Pending';
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
    
    // Toggle dark mode
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.body.classList.add('dark-theme');
                localStorage.setItem('darkMode', 'enabled');
            } else {
                document.body.classList.remove('dark-theme');
                localStorage.setItem('darkMode', 'disabled');
            }
        });
        
        // Check for saved dark mode preference
        const darkMode = localStorage.getItem('darkMode');
        if (darkMode === 'enabled') {
            darkModeToggle.checked = true;
            document.body.classList.add('dark-theme');
        }
    }
    
    // Apply user's dark mode preference from database
    const userDarkMode = document.body.getAttribute('data-dark-mode');
    if (userDarkMode === 'True') {
        document.body.classList.add('dark-theme');
        if (darkModeToggle) {
            darkModeToggle.checked = true;
        }
    }
    
    // Initialize date picker for due dates
    const dueDateInputs = document.querySelectorAll('.due-date-picker');
    if (dueDateInputs.length > 0) {
        dueDateInputs.forEach(input => {
            flatpickr(input, {
                dateFormat: "Y-m-d",
                minDate: "today"
            });
        });
    }
    
    // Task filter functionality
    const filterButtons = document.querySelectorAll('.filter-btn');
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function() {
                const filter = this.getAttribute('data-filter');
                
                // Remove active class from all buttons
                filterButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Show/hide tasks based on filter
                const tasks = document.querySelectorAll('.task-item');
                tasks.forEach(task => {
                    if (filter === 'all') {
                        task.style.display = 'block';
                    } else if (filter === 'completed') {
                        task.style.display = task.classList.contains('completed') ? 'block' : 'none';
                    } else if (filter === 'active') {
                        task.style.display = !task.classList.contains('completed') ? 'block' : 'none';
                    } else if (filter === 'today') {
                        const dueDate = task.getAttribute('data-due-date');
                        const today = new Date().toISOString().split('T')[0];
                        task.style.display = dueDate === today ? 'block' : 'none';
                    } else if (filter.startsWith('category-')) {
                        const category = filter.replace('category-', '');
                        const taskCategory = task.getAttribute('data-category');
                        task.style.display = taskCategory === category ? 'block' : 'none';
                    } else if (filter.startsWith('priority-')) {
                        const priority = filter.replace('priority-', '');
                        const taskPriority = task.getAttribute('data-priority');
                        task.style.display = taskPriority === priority ? 'block' : 'none';
                    }
                });
            });
        });
    }
    
    // Task search functionality
    const searchInput = document.getElementById('taskSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tasks = document.querySelectorAll('.task-item');
            
            tasks.forEach(task => {
                const title = task.querySelector('.task-title').textContent.toLowerCase();
                const description = task.querySelector('.task-description') ? 
                    task.querySelector('.task-description').textContent.toLowerCase() : '';
                
                if (title.includes(searchTerm) || description.includes(searchTerm)) {
                    task.style.display = 'block';
                } else {
                    task.style.display = 'none';
                }
            });
        });
    }
    
    // Initialize charts if Chart.js is available and canvas elements exist
    if (typeof Chart !== 'undefined') {
        // Category distribution chart
        const categoryCtx = document.getElementById('categoryChart');
        if (categoryCtx) {
            const categoryData = JSON.parse(categoryCtx.getAttribute('data-stats'));
            
            new Chart(categoryCtx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(categoryData),
                    datasets: [{
                        data: Object.values(categoryData),
                        backgroundColor: [
                            '#007bff', // work
                            '#28a745', // personal
                            '#ffc107', // shopping
                            '#dc3545', // health
                            '#17a2b8', // finance
                            '#6c757d'  // other
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        position: 'bottom',
                        labels: {
                            fontColor: document.body.classList.contains('dark-theme') ? '#e9ecef' : '#212529'
                        }
                    }
                }
            });
        }
        
        // Status distribution chart
        const statusCtx = document.getElementById('statusChart');
        if (statusCtx) {
            const statusData = JSON.parse(statusCtx.getAttribute('data-stats'));
            
            new Chart(statusCtx, {
                type: 'bar',
                data: {
                    labels: Object.keys(statusData),
                    datasets: [{
                        data: Object.values(statusData),
                        backgroundColor: [
                            '#ffc107', // pending
                            '#007bff', // in-progress
                            '#28a745'  // completed
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        display: false
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true,
                                fontColor: document.body.classList.contains('dark-theme') ? '#e9ecef' : '#212529'
                            }
                        }],
                        xAxes: [{
                            ticks: {
                                fontColor: document.body.classList.contains('dark-theme') ? '#e9ecef' : '#212529'
                            }
                        }]
                    }
                }
            });
        }
    }
});