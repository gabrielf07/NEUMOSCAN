document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM cargado, inicializando scripts...");

    // Referencias a elementos
    const loginToggle = document.getElementById('login-toggle');
    const registerToggle = document.getElementById('register-toggle');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (loginToggle && registerToggle && loginForm && registerForm) {
        // Toggle entre formularios
        loginToggle.addEventListener('click', function() {
            console.log("Click en Iniciar Sesión");
            this.classList.add('active');
            registerToggle.classList.remove('active');
            loginForm.classList.add('active');
            registerForm.classList.remove('active');
            hideMessage();
        });

        registerToggle.addEventListener('click', function() {
            console.log("Click en Registrarse");
            this.classList.add('active');
            loginToggle.classList.remove('active');
            registerForm.classList.add('active');
            loginForm.classList.remove('active');
            hideMessage();
        });
    } else {
        console.error("No se encontraron algunos elementos del formulario (IDs incorrectos?)");
    }

    // Manejo del inicio de sesión
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log("Enviando formulario de login...");

            const identificacion = document.getElementById('login-identificacion').value;
            const password = document.getElementById('login-password').value;
            
            if (!identificacion || !password) {
                showMessage('Completa todos los campos', 'error');
                return;
            }
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ identificacion, password })
                });

                const result = await response.json();

                showMessage(result.message, response.ok ? 'success' : 'error');
                
                if (response.ok) {
                    // ⚠️ CRÍTICO: Guarda la información del usuario en el almacenamiento local
                    localStorage.setItem('user', JSON.stringify(result.user));
                    setTimeout(() => {
                         window.location.href = result.redirect_url;
                    }, 1000); // Pequeño delay para ver el mensaje
                }

            } catch (error) {
                showMessage('Error de conexión con el servidor', 'error');
                console.error(error);
            }
        });
    }

    // Manejo del registro
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log("Enviando formulario de registro...");
            
            const primerNombre = document.getElementById('register-primer-nombre').value;
            const segundoNombre = document.getElementById('register-segundo-nombre').value;
            const primerApellido = document.getElementById('register-primer-apellido').value;
            const segundoApellido = document.getElementById('register-segundo-apellido').value;
            const cedula = document.getElementById('register-cedula').value;
            const email = document.getElementById('register-email').value;
            const telefono = document.getElementById('register-telefono').value;
            const especialidad = document.querySelector('input[name="especialidad"]:checked')?.value;
            const password = document.getElementById('register-password').value;
            const confirm = document.getElementById('register-confirm').value;
            
            // Validaciones básicas
            if (!primerNombre || !primerApellido || !cedula || !email || !telefono || !especialidad || !password || !confirm) {
                showMessage('Completa los campos obligatorios', 'error');
                return;
            }
            
            if (cedula.length < 8 || cedula.length > 10) {
                showMessage('La cédula debe tener entre 8 y 10 dígitos', 'error');
                return;
            }
            
            if (telefono.length !== 11 || !telefono.startsWith('04')) {
                showMessage('El teléfono debe tener 11 dígitos y comenzar con 04', 'error');
                return;
            }
            
            if (password !== confirm) {
                showMessage('Las contraseñas no coinciden', 'error');
                return;
            }
            
            if (password.length < 6) {
                showMessage('La contraseña debe tener al menos 6 caracteres', 'error');
                return;
            }
            
            const userData = {
                primer_nombre: primerNombre,
                segundo_nombre: segundoNombre,
                primer_apellido: primerApellido,
                segundo_apellido: segundoApellido,
                cedula: cedula,
                email: email,
                password: password,
                confirm_password: confirm,
                telefono: telefono,
                especialidad: especialidad
            };
            
            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });

                const result = await response.json();
                
                if (response.ok) {
                    showMessage(result.message, 'success');
                    localStorage.setItem('user', JSON.stringify(result.user));
                    setTimeout(() => {
                        window.location.href = result.redirect_url;
                    }, 1000);
                } else {
                    const errorMessage = result.detail || 'Error en el registro. Inténtelo de nuevo.';
                    showMessage(errorMessage, 'error');
                }

            } catch (error) {
                showMessage('Error de conexión con el servidor', 'error');
                console.error("Error:", error);
            }
        });
    }

    function showMessage(text, type) {
        const messageEl = document.getElementById('message');
        if (!messageEl) return;
        
        messageEl.textContent = text;
        messageEl.className = 'message ' + type;
        messageEl.style.display = 'block';
        
        if (type === 'success') {
            setTimeout(hideMessage, 5000);
        }
    }

    function hideMessage() {
        const messageEl = document.getElementById('message');
        if (messageEl) messageEl.style.display = 'none';
    }

    // Marcar campos obligatorios
    document.querySelectorAll('label').forEach(label => {
        if (label.htmlFor && document.getElementById(label.htmlFor)?.hasAttribute('required')) {
            label.classList.add('required-field');
        }
    });

    // Validación en tiempo real para teléfono
    const telInput = document.getElementById('register-telefono');
    if (telInput) {
        telInput.addEventListener('input', function(e) {
            const telefono = e.target.value;
            if (telefono.length > 0 && (!telefono.startsWith('04') || telefono.length !== 11)) {
                e.target.setCustomValidity('El teléfono debe comenzar con 04 y tener 11 dígitos');
            } else {
                e.target.setCustomValidity('');
            }
        });
    }

    // Validación en tiempo real para cédula
    const cedulaInput = document.getElementById('register-cedula');
    if (cedulaInput) {
        cedulaInput.addEventListener('input', function(e) {
            const cedula = e.target.value;
            if (cedula.length > 0 && (cedula.length < 8 || cedula.length > 10)) {
                e.target.setCustomValidity('La cédula debe tener entre 8 y 10 dígitos');
            } else {
                e.target.setCustomValidity('');
            }
        });
    }
});