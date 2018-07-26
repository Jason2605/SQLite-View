document.addEventListener('DOMContentLoaded', function() {
    let elem = document.querySelectorAll('.collapsible');
    M.Collapsible.init(elem, {});

    elem = document.querySelector('.tabs');
    M.Tabs.init(elem, {});

    elem = document.querySelectorAll('.dropdown-trigger');
    M.Dropdown.init(elem, {constrainWidth: false, coverTrigger: false});

    elem = document.querySelectorAll('.modal');
    M.Modal.init(elem, {});

    elem = document.querySelectorAll('select');
    M.FormSelect.init(elem, {});

    elem = document.querySelectorAll('.tooltipped');
    M.Tooltip.init(elem, {html: "You cant delete the primary key!"});
});

function replace_table(element) {

    let path = element.value;
    let id = element.id.split("-");

    let type = id[0];
    let page = id[1];

    axios.get(path + page).then(function (response) {
        let new_tbody = document.createElement('tbody');
        new_tbody.id = "sql-data";
        let data = response.data.data;

        for (let i = 0; i < data.length; i++) {
            let row = new_tbody.insertRow();
            for (let j = 0; j < data[i].length; j++) {
                let cell = row.insertCell(j);
                cell.innerText = data[i][j];
                cell.className = (j + 1).toString();
            }
        }

        if (type === "previous") {
            document.getElementById("next-" + (parseInt(page) + 2)).disabled = (data.length < 50);
        } else {
            document.getElementById("next-" + page).disabled = (data.length < 50);
        }


        if (data.length !== 0) {
            let table = document.getElementById("sql-data");
            table.parentNode.replaceChild(new_tbody, table);

            after_get();
        }

    });

    function after_get() {
        page = parseInt(page);

        if (type === "previous") {
            element.id = "previous-" + (page - 1);
            document.getElementById('next-' + (page + 2)).id = "next-" + (page + 1);
        } else {
            element.id = "next-" + (page + 1);
            document.getElementById('previous-' + (page - 2)).id = "previous-" + (page - 1);
        }

        document.getElementById("previous-" + (page - 1)).disabled = (page === 1);
    }
}

function replace_json(element) {

    let path = element.value;
    let id = element.id.split("-");

    let type = id[0];
    let page = id[1];

    axios.get(path + page + "/json/").then(function (response) {
        let length = response.data.length;
        console.log(length);

        if (type === "previous_json") {
            document.getElementById("next_json-" + (parseInt(page) + 2)).disabled = (length < 50);
        } else {
            document.getElementById("next_json-" + page).disabled = (length < 50);
        }

        if (length !== 0) {
            document.getElementById("json_data").innerText = response.data.data;
            after_get();
        }
    });

    function after_get() {
        page = parseInt(page);

        if (type === "previous_json") {
            element.id = "previous_json-" + (page - 1);
            document.getElementById('next_json-' + (page + 2)).id = "next_json-" + (page + 1);
        } else {
            element.id = "next_json-" + (page + 1);
            document.getElementById('previous_json-' + (page - 2)).id = "previous_json-" + (page - 1);
        }

        document.getElementById("previous_json-" + (page - 1)).disabled = (page === 1);
    }
}

function toggle_table(element, column, event) {
    event.preventDefault();
    element = element.firstElementChild.firstElementChild.firstElementChild;
    element.checked = !element.checked;
    let elements = document.getElementsByClassName(column);
    let display_element = element.checked ? "table-cell" : "none";

    [].forEach.call(elements, function (element) {
        element.style.display = display_element;
    });
}

function filter_table() {
    let tbody_rows = document.getElementById("sql-data").getElementsByTagName("tr");
    let search = document.getElementById("search").value;

    for (let i = 0; i < tbody_rows.length; i++) {
        let table_data = tbody_rows[i].getElementsByTagName("td");
        let hide_row = true;

        for (let j = 0; j < table_data.length; j++) {
            if (table_data[j].style.display !== "none") {
                if (table_data[j].innerText.indexOf(search) > -1) {
                    hide_row = false;
                    break;
                }
            }
        }

        tbody_rows[i].style.display = hide_row ? "none" : "";
    }
}

function populate_modal(column) {
    document.getElementById("column-rename-old").value = column;
    document.getElementById("column-rename").value = column;
    document.getElementById("column-rename-label").className = "active";
}