document.addEventListener("DOMContentLoaded", () => {
    // Verificar si hay un usuario logueado
    const user = JSON.parse(localStorage.getItem("user"));
  
    // ⚠️ CRÍTICO: Muestra el objeto de usuario en la consola para depuración
    console.log("Objeto de usuario del localStorage:", user);
  
    if (!user || Object.keys(user).length === 0) {
      localStorage.removeItem("user"); // Limpia el dato corrupto o vacío
      window.location.href = "/";
      return;
    }
  
    // Actualizar la información del usuario en la barra lateral
    const doctorName =
      user.primer_nombre && user.primer_apellido
        ? `${user.primer_nombre} ${user.primer_apellido}`
        : "Usuario";
    const doctorSpecialty = user.especialidad
      ? user.especialidad
          .replace("_", " ")
          .replace(/\b\w/g, (l) => l.toUpperCase())
      : "Especialidad";
  
    document.getElementById("doctor-name").textContent = `Dr. ${doctorName}`;
    document.getElementById("doctor-specialty").textContent = doctorSpecialty;
    // document.getElementById("welcome-doctor-name").textContent = doctorName; // No necesario en pacientes.html si no hay esa sección
  
    // Lógica de navegación del sidebar (Adaptado para enlaces reales)
    const navItems = document.querySelectorAll(".nav-item");
    const sections = document.querySelectorAll(".content-section");
    const sectionTitle = document.getElementById("section-title");
  
    navItems.forEach((item) => {
      item.addEventListener("click", (e) => {
        // Permitir navegación normal si el href no es "#"
        const href = item.getAttribute("href");
        if (href && href !== "#") {
          return; // Dejar que el navegador siga el enlace
        }
  
        e.preventDefault();
  
        navItems.forEach((nav) => nav.classList.remove("active"));
        sections.forEach((sec) => sec.classList.remove("active"));
  
        const targetSectionId = e.currentTarget.dataset.section + "-section";
        const targetElement = document.getElementById(targetSectionId);
        const currentButton = e.currentTarget;
  
        if (targetElement) {
          currentButton.classList.add("active");
          targetElement.classList.add("active");
          if(sectionTitle) sectionTitle.textContent = currentButton.querySelector("span").textContent;
  
          // Restablecer el formulario de pacientes al cambiar a esa sección
          if (currentButton.dataset.section === "patients") {
            const addPatientToggleBtn =
              document.getElementById("add-patient-toggle");
            if (addPatientToggleBtn) {
              document
                .querySelectorAll("#patients-section .form")
                .forEach((form) => form.classList.remove("active"));
              document
                .querySelectorAll("#patients-section .toggle-btn")
                .forEach((btn) => btn.classList.remove("active"));
              document.getElementById("add-patient-form").classList.add("active");
              addPatientToggleBtn.classList.add("active");
  
              // Limpiar el formulario y el mensaje al cambiar de sección
              if (addPatientForm) addPatientForm.reset();
              if (patientMessageDiv) hideMessage(patientMessageDiv);
            }
          }
        } else {
          console.error(
            `Error: No se encontró la sección con ID ${targetSectionId}`
          );
        }
      });
    });
  
    // Lógica del formulario de pacientes
    const addPatientToggleBtn = document.getElementById("add-patient-toggle");
    const viewPatientsToggleBtn = document.getElementById("view-patients-toggle");
    const addPatientForm = document.getElementById("add-patient-form");
    const patientListDiv = document.getElementById("patient-list");
    const noPatientsMessage = document.getElementById("no-patients-message");
    const patientMessageDiv = document.getElementById("patient-message");
    const viewPatientsSection = document.getElementById("view-patients-section"); 
  
    // Función auxiliar para mostrar/ocultar formularios de pacientes
    function togglePatientForms(activeFormId) {
      // Ocultar todos los formularios y desactivar todos los toggles
      document
        .querySelectorAll("#patients-section .form")
        .forEach((form) => form.classList.remove("active"));
      document
        .querySelectorAll("#patients-section .toggle-btn")
        .forEach((btn) => btn.classList.remove("active"));
  
      // Mostrar el formulario activo y activar su toggle correspondiente
      const activeForm = document.getElementById(activeFormId);
      const correspondingToggle = document.getElementById(
        activeFormId.replace(/-form|-section/g, "") + "-toggle"
      );
  
      if (activeForm) activeForm.classList.add("active");
      if (correspondingToggle) correspondingToggle.classList.add("active");
    }
  
    // Función auxiliar para mostrar mensajes
    function showMessage(element, text, type) {
      if (!element) return; 
      element.textContent = text;
      element.className = "message " + type;
      element.style.display = "block";
    }
  
    // Función auxiliar para ocultar mensajes
    function hideMessage(element) {
      if (!element) return;
      element.style.display = "none";
    }
  
    // Lógica para el toggle de pacientes
    if (addPatientToggleBtn)
      addPatientToggleBtn.addEventListener("click", () => {
        togglePatientForms("add-patient-form");
        hideMessage(patientMessageDiv);
        if (addPatientForm) addPatientForm.reset(); 
      });
  
    if (viewPatientsToggleBtn)
      viewPatientsToggleBtn.addEventListener("click", () => {
        togglePatientForms("view-patients-section"); 
        fetchPatients();
      });
  
    // Manejar el envío del formulario de nuevo paciente
    if (addPatientForm)
      addPatientForm.addEventListener("submit", async (e) => {
        e.preventDefault();
  
        const cedulaInput = document.getElementById("patient-cedula");
        const telefonoInput = document.getElementById("patient-telefono");
        const emailInput = document.getElementById("patient-email");
        const requiredFields = [
          document.getElementById("patient-primer-nombre"),
          document.getElementById("patient-primer-apellido"),
          cedulaInput,
          telefonoInput,
        ];
  
        // Verificar que todos los campos obligatorios estén llenos
        if (requiredFields.some((field) => !field || !field.value)) {
          showMessage(
            patientMessageDiv,
            "Por favor, complete todos los campos obligatorios.",
            "error"
          );
          return;
        }
  
        if (!addPatientForm.reportValidity()) {
          showMessage(
            patientMessageDiv,
            "Por favor, corrija los datos para guardar el paciente.",
            "error"
          );
          return;
        }
  
        const newPatient = {
          doctor_id: user.id,
          primer_nombre: requiredFields[0].value,
          segundo_nombre:
            document.getElementById("patient-segundo-nombre").value || "", 
          primer_apellido: requiredFields[1].value,
          segundo_apellido:
            document.getElementById("patient-segundo-apellido").value || "", 
          cedula: cedulaInput.value,
          telefono: telefonoInput.value,
          email: emailInput ? emailInput.value : "", 
        };
  
        try {
          const response = await fetch("/add-patient", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newPatient),
          });
  
          const result = await response.json();
  
          if (response.ok) {
            showMessage(patientMessageDiv, result.message, "success");
            addPatientForm.reset();
            setTimeout(() => hideMessage(patientMessageDiv), 3000); 
          } else {
            showMessage(
              patientMessageDiv,
              result.detail || "Error al registrar el paciente.",
              "error"
            );
          }
        } catch (error) {
          console.error("Error en fetch /add-patient:", error);
          showMessage(
            patientMessageDiv,
            "Error de conexión con el servidor.",
            "error"
          );
        }
      });
  
    // Función para obtener y mostrar los pacientes
    async function fetchPatients() {
      if (!patientListDiv || !noPatientsMessage) {
        console.error(
          "Error: Elementos patientListDiv o noPatientsMessage no encontrados."
        );
        return;
      }
      try {
        const response = await fetch(`/patients/${user.id}`);
        if (!response.ok) {
          throw new Error(
            `Error HTTP ${response.status}: ${response.statusText}`
          );
        }
        const patients = await response.json();
  
        patientListDiv.innerHTML = ""; 
        if (patients.length === 0) {
          noPatientsMessage.style.display = "block";
        } else {
          noPatientsMessage.style.display = "none";
          patients.forEach((patient) => {
            const patientCard = document.createElement("div");
            patientCard.className = "patient-card";
            const patientKey = patient.id || patient.cedula;
            patientCard.innerHTML = `
                          <h4>${patient.primer_nombre} ${
              patient.primer_apellido
            }</h4>
                          <p><strong>Cédula:</strong> ${patient.cedula}</p>
                          <p><strong>Teléfono:</strong> ${patient.telefono}</p>
                          <p><strong>Email:</strong> ${patient.email || "N/A"}</p>
                          `;
            patientListDiv.appendChild(patientCard);
          });
        }
      } catch (error) {
        console.error("Error fetching patients:", error);
        if (patientListDiv)
          patientListDiv.innerHTML =
            '<p class="message error">Error al cargar la lista de pacientes.</p>';
        if (noPatientsMessage) noPatientsMessage.style.display = "none"; 
      }
    }
  
    // Lógica para el logout
    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn)
      logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("user");
        window.location.href = "/";
      });
  
  });
