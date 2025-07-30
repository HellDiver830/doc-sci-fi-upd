let token = null;
let role = null;
let currentSubject = null;
let currentData = null;

function login() {
    let username = document.getElementById('username').value;
    let password = document.getElementById('password').value;
    eel.login(username, password)(function(res){
        if(res.success) {
            alert("Успешный вход, роль: " + res.role);
            token = eel.token; 
            role = res.role;
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('app').style.display = 'block';
            if(res.role === 'teacher' || res.role === 'superadmin') {
                document.getElementById('teacher-panel').style.display = 'block';
            }
            if(res.role === 'superadmin') {
                document.getElementById('superadmin-panel').style.display = 'block';
                
            }
        } else {
            alert(res.error);
        }
    });
}

function registerUser() {
    let username = document.getElementById('reg_username').value;
    let password = document.getElementById('reg_password').value;
    let email = document.getElementById('reg_email').value;
    eel.register(username, password, email)(function(res){
        if(res.success) {
            alert("Пользователь зарегистрирован");
        } else {
            alert(res.error);
        }
    });
}

function loadSubjects() {
    eel.list_subjects()(function(subjects){
        let select = document.getElementById('subject-select');
        select.innerHTML = '';
        if(subjects && subjects.length > 0) {
            subjects.forEach(s => {
                let opt = document.createElement('option');
                opt.value = s;
                opt.text = s;
                select.appendChild(opt);
            });
        } else {
            alert("Нет доступных предметов или у вас нет доступа.");
        }
    });
}

function loadSelectedCourse() {
    let subject = document.getElementById('subject-select').value;
    currentSubject = subject;
    eel.get_course(subject)(function(data){
        if(data.error) {
            alert(data.error);
            return;
        }
        currentData = data;
        document.getElementById('course-name').innerText = data.Name || "Без имени";
        displayCourseData(data);
        if(document.getElementById('teacher-panel').style.display === 'block') {
            document.getElementById('course-data').value = JSON.stringify(data, null, 4);
        }
    });
}

function updateCourse() {
    let subject = document.getElementById('subject-select').value;
    let data = document.getElementById('course-data').value;
    try {
        let jsonData = JSON.parse(data);
        eel.update_course(subject, jsonData)(function(res){
            if(res.success) {
                alert("Данные обновлены");
                loadSelectedCourse();
            } else {
                alert(res.error || "Ошибка обновления");
            }
        });
    } catch(e) {
        alert("Некорректный JSON");
    }
}

function editFieldUI() {
    let subject = document.getElementById('subject-select').value;
    let field = document.getElementById('edit-field-name').value;
    let value = document.getElementById('edit-field-value').value;
    eel.edit_field(subject, field, value)(function(res){
        if(res.success) {
            alert("Поле обновлено");
            loadSelectedCourse();
        } else {
            alert(res.error || "Ошибка");
        }
    });
}

function generateDocUI(docType) {
    let subject = document.getElementById('subject-select').value;
    eel.generate_doc(subject, docType)(function(res){
        if(res.success) {
            alert("Документ создан: "+res.doc_path);
        } else {
            alert(res.error||"Ошибка при генерации документа");
        }
    });
}

function generateDocBiletsUI() {
    let subject = document.getElementById('subject-select').value;
    let count = prompt("Сколько билетов?", "5");
    eel.generate_doc(subject, "bilets", parseInt(count))(function(res){
        if(res.success) {
            alert("Документ с билетами: "+res.doc_path);
        } else {
            alert(res.error||"Ошибка при генерации билетов");
        }
    });
}

function loadUsers() {
    eel.get_users()(function(res){
        let div = document.getElementById('users-list');
        div.innerHTML = '';
        if(res.error) {
            alert(res.error);
            return;
        }

        if(Array.isArray(res)) {
            res.forEach(u => {
                let p = document.createElement('p');
                p.textContent = `Username: ${u.username}, Email: ${u.email}, Role: ${u.role}, Subjects: ${JSON.stringify(u.subjects)}`;
                div.appendChild(p);
            });
        } else {
            alert("Ошибка получения списка пользователей");
        }
    });
}

function changeUserRole() {
    let username = document.getElementById('change-role-username').value;
    let newrole = document.getElementById('change-role-newrole').value;
    eel.update_user_role(username, newrole)(function(res){
        if(res.success) {
            alert("Роль обновлена");
        } else {
            alert(res.error || "Ошибка");
        }
    });
}

function assignSubjects() {
    let username = document.getElementById('assign-subjects-username').value;
    let subjectsStr = document.getElementById('assign-subjects-list').value;
    try {
        let subjects = JSON.parse(subjectsStr);
        eel.assign_subjects(username, subjects)(function(res){
            if(res.success) {
                alert("Предметы назначены");
            } else {
                alert(res.error || "Ошибка");
            }
        });
    } catch(e) {
        alert("Некорректный JSON с предметами");
    }
}

function makeEditableCell(td, fieldName, fieldValue) {
    td.innerHTML = '';
    let input = document.createElement('input');
    input.type = 'text';
    input.className = 'editable-input';
    input.value = fieldValue;

    let saveBtn = document.createElement('button');
    saveBtn.textContent = 'Сохранить';
    saveBtn.className = 'save-btn';
    saveBtn.onclick = function() {
        eel.edit_field(currentSubject, fieldName, input.value)(function(res){
            if(res.success) {
                alert("Поле обновлено");
                loadSelectedCourse();
            } else {
                alert(res.error||"Ошибка");
            }
        });
    }

    td.appendChild(input);
    td.appendChild(saveBtn);
}

function cellClicked(e) {
    let td = e.currentTarget;
    let fieldName = td.getAttribute('data-field');
    let fieldValue = td.getAttribute('data-value');
    makeEditableCell(td, fieldName, fieldValue);
}

function displayCourseData(data) {
    let container = document.getElementById('course-view');
    container.innerHTML = '';

    let isEditable = (role === 'teacher' || role === 'superadmin');

    let infoTable = document.createElement('table');
    infoTable.className = 'data-table';
    let fields = ["Faculty", "Chair", "Name", "EducationProgram", "TrainingDirection", "Degree", "Annote", "Aims", "PlaceInStructure", "Background"];
    fields.forEach(f => {
        if(data[f] !== undefined) {
            let tr = document.createElement('tr');
            let td1 = document.createElement('td');
            td1.textContent = f;
            let td2 = document.createElement('td');
            td2.setAttribute('data-field', f);
            td2.setAttribute('data-value', data[f]);
            if(isEditable) {
                td2.classList.add('editable-cell');
                td2.addEventListener('click', cellClicked);
            }
            td2.textContent = data[f];
            tr.appendChild(td1);
            tr.appendChild(td2);
            infoTable.appendChild(tr);
        }
    });
    container.appendChild(infoTable);

    // Можно добавить отображение Semester, StructureAndContents и т.д.
    // Для краткости оставим как есть.
}
