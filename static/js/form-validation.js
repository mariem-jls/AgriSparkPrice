// Validation des formulaires
document.addEventListener('DOMContentLoaded', function() {
    // Validation pour le formulaire de recommandation de cultures
    const cropForm = document.querySelector('.crop-form form');
    if (cropForm) {
        cropForm.addEventListener('submit', function(e) {
            let isValid = true;
            const inputs = this.querySelectorAll('input[type="number"]');
            
            inputs.forEach(input => {
                const min = parseFloat(input.min);
                const max = parseFloat(input.max);
                const value = parseFloat(input.value);
                
                if (value < min || value > max) {
                    isValid = false;
                    showError(input, `Valeur doit être entre ${min} et ${max}`);
                } else {
                    clearError(input);
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
    
    // Validation pour le formulaire de prédiction de prix
    const priceForm = document.querySelector('.price-form form');
    if (priceForm) {
        priceForm.addEventListener('submit', function(e) {
            const yearInput = this.querySelector('input[name="base_year"]');
            const currentYear = new Date().getFullYear();
            
            if (parseInt(yearInput.value) > currentYear) {
                showError(yearInput, "L'année de base ne peut pas être dans le futur");
                e.preventDefault();
            }
        });
    }
    
    // Affichage des erreurs
    function showError(input, message) {
        clearError(input);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-error';
        errorDiv.style.color = '#e74c3c';
        errorDiv.style.fontSize = '0.85rem';
        errorDiv.style.marginTop = '5px';
        errorDiv.textContent = message;
        
        input.style.borderColor = '#e74c3c';
        input.parentNode.appendChild(errorDiv);
    }
    
    function clearError(input) {
        input.style.borderColor = '';
        const errorDiv = input.parentNode.querySelector('.form-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
    
    // Animation des barres de probabilité
    const probabilityBars = document.querySelectorAll('.probability-fill');
    probabilityBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0';
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });
    
    // Gestion du drag and drop pour l'upload d'image
    const fileInput = document.querySelector('.file-input');
    if (fileInput) {
        const uploadContainer = fileInput.closest('.upload-container');
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadContainer.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadContainer.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadContainer.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            uploadContainer.style.borderColor = 'var(--primary-green)';
            uploadContainer.style.background = 'var(--primary-light)';
        }
        
        function unhighlight() {
            uploadContainer.style.borderColor = '';
            uploadContainer.style.background = '';
        }
        
        uploadContainer.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;
            
            // Déclencher l'événement change
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
        }
    }
});