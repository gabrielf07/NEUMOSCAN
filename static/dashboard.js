document.addEventListener("DOMContentLoaded", () => {
  // Verificar si hay un usuario logueado
  const user = JSON.parse(localStorage.getItem("user"));

    // ⚠️ CRÍTICO: Muestra el objeto de usuario en la consola para depuración
    console.log("Objeto de usuario del localStorage:", user);

    if (!user || Object.keys(user).length === 0) {
        localStorage.removeItem('user'); // Limpia el dato corrupto o vacío
        window.location.href = '/';
        return;
    }

    // Actualizar la información del usuario en la barra lateral
    // Corrección: Usar primer_nombre y primer_apellido del objeto user
    const doctorName = (user.primer_nombre && user.primer_apellido) ? `${user.primer_nombre} ${user.primer_apellido}` : 'Usuario';
    const doctorSpecialty = user.especialidad ? user.especialidad.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Especialidad';

    document.getElementById('doctor-name').textContent = `Dr. ${doctorName}`;
    document.getElementById('doctor-specialty').textContent = doctorSpecialty;
    document.getElementById('welcome-doctor-name').textContent = doctorName;

    // Lógica de navegación del sidebar
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.content-section');
    const sectionTitle = document.getElementById('section-title');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();

            navItems.forEach(nav => nav.classList.remove('active'));
            sections.forEach(sec => sec.classList.remove('active'));

            const targetSectionId = e.currentTarget.dataset.section + '-section';
            const targetElement = document.getElementById(targetSectionId);
            const currentButton = e.currentTarget;

            if (targetElement) {
                currentButton.classList.add('active');
                targetElement.classList.add('active');
                sectionTitle.textContent = currentButton.querySelector('span').textContent;

                // Restablecer el formulario de pacientes al cambiar a esa sección
                if (currentButton.dataset.section === 'patients') {
                    const addPatientToggleBtn = document.getElementById('add-patient-toggle');
                    if(addPatientToggleBtn){
                        document.querySelectorAll('#patients-section .form').forEach(form => form.classList.remove('active'));
                        document.querySelectorAll('#patients-section .toggle-btn').forEach(btn => btn.classList.remove('active'));
                        document.getElementById('add-patient-form').classList.add('active');
                        addPatientToggleBtn.classList.add('active');

                        // Limpiar el formulario y el mensaje al cambiar de sección
                        if(addPatientForm) addPatientForm.reset();
                        if(patientMessageDiv) hideMessage(patientMessageDiv);
                    }
                }
            } else {
                console.error(`Error: No se encontró la sección con ID ${targetSectionId}`);
            }
        });
    });

    // Lógica del formulario de pacientes
    const addPatientToggleBtn = document.getElementById('add-patient-toggle');
    const viewPatientsToggleBtn = document.getElementById('view-patients-toggle');
    const addPatientForm = document.getElementById('add-patient-form');
    const patientListDiv = document.getElementById('patient-list');
    const noPatientsMessage = document.getElementById('no-patients-message');
    const patientMessageDiv = document.getElementById('patient-message');
    const viewPatientsSection = document.getElementById('view-patients-section'); // Añadir referencia a la sección

    // Función auxiliar para mostrar/ocultar formularios de pacientes
    function togglePatientForms(activeFormId) {
        // Ocultar todos los formularios y desactivar todos los toggles
        document.querySelectorAll('#patients-section .form').forEach(form => form.classList.remove('active'));
        document.querySelectorAll('#patients-section .toggle-btn').forEach(btn => btn.classList.remove('active'));

        // Mostrar el formulario activo y activar su toggle correspondiente
        const activeForm = document.getElementById(activeFormId);
        const correspondingToggle = document.getElementById(activeFormId.replace(/-form|-section/g, '') + '-toggle');

        if(activeForm) activeForm.classList.add('active');
        if(correspondingToggle) correspondingToggle.classList.add('active');

    }

    // Función auxiliar para mostrar mensajes
    function showMessage(element, text, type) {
        if (!element) return; // Añadir verificación
        element.textContent = text;
        element.className = 'message ' + type;
        element.style.display = 'block';
    }

    // Función auxiliar para ocultar mensajes
    function hideMessage(element) {
        if (!element) return; // Añadir verificación
        element.style.display = 'none';
    }

    // Lógica para el toggle de pacientes
    if (addPatientToggleBtn) addPatientToggleBtn.addEventListener('click', () => {
        togglePatientForms('add-patient-form');
        hideMessage(patientMessageDiv);
        if(addPatientForm) addPatientForm.reset(); // Limpiar el formulario al volver a él
    });

    if (viewPatientsToggleBtn) viewPatientsToggleBtn.addEventListener('click', () => {
        togglePatientForms('view-patients-section'); // Cambiado a ID de la sección
        fetchPatients();
    });

    // Manejar el envío del formulario de nuevo paciente
    if (addPatientForm) addPatientForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // ⚠️ Añadida validación básica en el frontend
        const cedulaInput = document.getElementById('patient-cedula');
        const telefonoInput = document.getElementById('patient-telefono');
        const emailInput = document.getElementById('patient-email');
        const requiredFields = [
            document.getElementById('patient-primer-nombre'),
            document.getElementById('patient-primer-apellido'),
            cedulaInput, telefonoInput
        ];

        // Verificar que todos los campos obligatorios estén llenos
        if (requiredFields.some(field => !field || !field.value)) { // Añadida verificación de existencia del campo
            showMessage(patientMessageDiv, 'Por favor, complete todos los campos obligatorios.', 'error');
            return;
        }

        // ⚠️ El método reportValidity() fuerza la revalidación del formulario
        if (!addPatientForm.reportValidity()) {
            showMessage(patientMessageDiv, 'Por favor, corrija los datos para guardar el paciente.', 'error');
            return;
        }

        const newPatient = {
            doctor_id: user.id,
            primer_nombre: requiredFields[0].value,
            segundo_nombre: document.getElementById('patient-segundo-nombre').value || "", // Asegurar que sea string
            primer_apellido: requiredFields[1].value,
            segundo_apellido: document.getElementById('patient-segundo-apellido').value || "", // Asegurar que sea string
            cedula: cedulaInput.value,
            telefono: telefonoInput.value,
            email: emailInput ? emailInput.value : "" // Asegurar que exista emailInput
        };

        try {
            const response = await fetch('/add-patient', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newPatient)
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(patientMessageDiv, result.message, 'success');
                //  Reiniciar el formulario después de un registro exitoso
                addPatientForm.reset();
                setTimeout(() => hideMessage(patientMessageDiv), 3000); // Ocultar mensaje de éxito
            } else {
                showMessage(patientMessageDiv, result.detail || "Error al registrar el paciente.", 'error');
            }
        } catch (error) {
            console.error("Error en fetch /add-patient:", error);
            showMessage(patientMessageDiv, 'Error de conexión con el servidor.', 'error');
        }
    });

    // Función para obtener y mostrar los pacientes
    async function fetchPatients() {
        // Asegurarse de que los elementos existan antes de usarlos
        if (!patientListDiv || !noPatientsMessage) {
             console.error("Error: Elementos patientListDiv o noPatientsMessage no encontrados.");
             return;
        }
        try {
            const response = await fetch(`/patients/${user.id}`);
            if (!response.ok) {
                throw new Error(`Error HTTP ${response.status}: ${response.statusText}`);
            }
            const patients = await response.json();

            patientListDiv.innerHTML = ''; // Limpiar lista
            if (patients.length === 0) {
                noPatientsMessage.style.display = 'block';
            } else {
                noPatientsMessage.style.display = 'none';
                patients.forEach(patient => {
                    const patientCard = document.createElement('div');
                    patientCard.className = 'patient-card';
                    // Usar patient.id si está disponible, o cedula como fallback key
                    const patientKey = patient.id || patient.cedula;
                    patientCard.innerHTML = `
                        <h4>${patient.primer_nombre} ${patient.primer_apellido}</h4>
                        <p><strong>Cédula:</strong> ${patient.cedula}</p>
                        <p><strong>Teléfono:</strong> ${patient.telefono}</p>
                        <p><strong>Email:</strong> ${patient.email || 'N/A'}</p>
                        `;
                    patientListDiv.appendChild(patientCard);
                });
            }
        } catch (error) {
            console.error('Error fetching patients:', error);
            if(patientListDiv) patientListDiv.innerHTML = '<p class="message error">Error al cargar la lista de pacientes.</p>';
            if(noPatientsMessage) noPatientsMessage.style.display = 'none'; // Ocultar mensaje 'no hay pacientes'
        }
    }


    // Lógica para el logout
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('user');
        window.location.href = '/';
    });

    // =============================================================
    //      🩺 INICIO: LÓGICA PARA EVALUACIÓN DE RADIOGRAFÍAS 🩺
    // =============================================================

    const evaluationForm = document.getElementById('evaluation-form');
    const xrayFileInput = document.getElementById('xray-file');
    const imagePreview = document.getElementById('image-preview'); // Para previsualización
    const resultDiv = document.getElementById('evaluation-result');
    const resultText = document.getElementById('result-text');
    const resultConfidence = document.getElementById('result-confidence');
    const resultDetail = document.getElementById('result-detail');
    const evaluationMessage = document.getElementById('evaluation-message');
    const resultOriginalImage = document.getElementById('result-original-image'); // Imagen original en resultado
    const resultHeatmapImage = document.getElementById('result-heatmap-image'); // Imagen heatmap en resultado

    // --- Lógica para la Previsualización ---
    if (xrayFileInput && imagePreview) {
        xrayFileInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();

                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block'; // Mostrar la previsualización
                }
                reader.readAsDataURL(file); // Leer el archivo como URL de datos
            } else {
                imagePreview.src = '#'; // Limpiar src
                imagePreview.style.display = 'none'; // Ocultar si no es imagen válida
            }
        });
    }

    // --- Manejo del envío del formulario de evaluación ---
    if (evaluationForm) {
        evaluationForm.addEventListener('submit', (e) => { // No necesita async aquí
            e.preventDefault();

            if (!xrayFileInput.files || xrayFileInput.files.length === 0) {
                showMessage(evaluationMessage, 'Por favor, selecciona un archivo de imagen.', 'error');
                return;
            }

            const file = xrayFileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);

            // Leer la imagen para mostrarla en resultados USANDO FileReader
            const readerForResult = new FileReader();
            readerForResult.onload = () => {
                // Guardamos la URL de datos para usarla después de la predicción
                const imageDataUrl = readerForResult.result;
                // Llamamos a la función que hace el fetch DESPUÉS de leer la imagen
                submitEvaluation(formData, imageDataUrl);
            };
            readerForResult.onerror = () => {
                 showMessage(evaluationMessage, 'Error al leer la imagen para mostrar resultados.', 'error');
                 // Habilitar botón si falla la lectura
                 const submitButton = evaluationForm.querySelector('button[type="submit"]');
                 if(submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = 'Analizar Radiografía';
                 }
            }
            readerForResult.readAsDataURL(file); // Iniciar lectura
        });
    }

    // --- Función Separada para Enviar y Manejar Respuesta ---
    async function submitEvaluation(formData, imageDataUrl) {
        const submitButton = evaluationForm.querySelector('button[type="submit"]');

        // Mostrar "cargando..." y deshabilitar botón
        showMessage(evaluationMessage, 'Analizando imagen, por favor espera...', 'success');
        if(resultDiv) resultDiv.style.display = 'none';
        if(submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Analizando...';
        }

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

        if (response.ok) {
            // --- MOSTRAR RESULTADOS (VERSIÓN CORREGIDA Y CON DEPURACIÓN) ---
            console.log("Respuesta del backend (/predict):", result); // DEBUG: Mira qué llega

            // Actualizar Textos
            if(resultText) {
                resultText.textContent = result.resultado || "Resultado no disponible"; // Añadir fallback
                // Colorear texto
                if (result.resultado && result.resultado.toLowerCase().includes("neumonía")) {
                    resultText.style.color = 'var(--error)';
                } else {
                    resultText.style.color = 'var(--success)';
                }
            } else {
                console.error("Elemento result-text no encontrado");
            }

            if(resultConfidence) {
                resultConfidence.textContent = result.confianza || "N/A"; // Añadir fallback
            } else {
                console.error("Elemento result-confidence no encontrado");
            }

            if(resultDetail) {
                // Formatear detalle (con verificación)
                const detailString = result.detalle ? Object.entries(result.detalle)
                                                .map(([key, value]) => `${key}: ${value}`)
                                                .join(', ') : 'No disponible';
                resultDetail.textContent = `(${detailString})`;
            } else {
                console.error("Elemento result-detail no encontrado");
            }

            // Actualizar Imagen Original
            if(resultOriginalImage) {
                if (imageDataUrl) {
                    console.log("DEBUG: Estableciendo src de imagen original."); // DEBUG
                    resultOriginalImage.src = imageDataUrl;
                } else {
                    console.error("Error: imageDataUrl está vacía al intentar mostrar imagen original.");
                    resultOriginalImage.src = '#'; // Indicar error o poner placeholder
                    resultOriginalImage.alt = 'Error al cargar imagen original';
                }
            } else {
                console.error("Elemento result-original-image no encontrado");
            }

            // Actualizar Imagen Heatmap/Placeholder
            if(resultHeatmapImage) {
                const heatmapSmallText = resultHeatmapImage.nextElementSibling; // El texto <small>
                if (result.heatmap_base64) {
                    console.log("DEBUG: Estableciendo src de imagen heatmap."); // DEBUG
                    resultHeatmapImage.src = 'data:image/png;base64,' + result.heatmap_base64;
                    if(heatmapSmallText && heatmapSmallText.tagName === 'SMALL') {
                        heatmapSmallText.style.display = 'none'; // Ocultar "(Visualización...)"
                    }
                } else {
                    // No hay heatmap, mostrar original como placeholder
                    console.log("DEBUG: No se recibió heatmap, mostrando original como placeholder."); // DEBUG
                    resultHeatmapImage.src = imageDataUrl || '#'; // Usar original o fallback
                    if(heatmapSmallText && heatmapSmallText.tagName === 'SMALL') {
                        heatmapSmallText.style.display = 'block'; // Mostrar "(Visualización...)"
                    }
                }
            } else {
                console.error("Elemento result-heatmap-image no encontrado");
            }

            // Mostrar el div de resultados y limpiar formulario
            if(resultDiv) resultDiv.style.display = 'block';
            hideMessage(evaluationMessage);
            if(evaluationForm) evaluationForm.reset();
            if(imagePreview) imagePreview.style.display = 'none'; // Ocultar previsualización
            // --- FIN MOSTRAR RESULTADOS ---
            } else {
                showMessage(evaluationMessage, result.detail || 'Error en la predicción del servidor.', 'error');
            }
        } catch (error) {
            console.error("Error en fetch /predict:", error);
            showMessage(evaluationMessage, 'Error de conexión con el servidor al analizar.', 'error');
        } finally {
             // Volver a habilitar el botón siempre
             if(submitButton) {
                 submitButton.disabled = false;
                 submitButton.textContent = 'Analizar Radiografía';
             }
        }
    }
    

}); 