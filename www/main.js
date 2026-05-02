$(document).ready(function () {

    eel.init()()

    $('.text').textillate({
        loop: true,
        sync: true,
        in: {
            effect: "bounceIn",
        },
        out: {
            effect: "bounceOut",
        },

    });

    // Siri configuration
    var siriWave = new SiriWave({
        container: document.getElementById("siri-container"),
        width: 800,
        height: 200,
        style: "ios9",
        amplitude: "1",
        speed: "0.30",
        autostart: true
    });

    // Siri message animation
    $('.siri-message').textillate({
        loop: true,
        sync: true,
        in: {
            effect: "fadeInUp",
            sync: true,
        },
        out: {
            effect: "fadeOutUp",
            sync: true,
        },

    });

    // mic button click event
    $("#MicBtn").click(function () {
        eel.playAssistantSound()
        $("#Oval").attr("hidden", true);
        $("#SiriWave").attr("hidden", false);
        eel.allCommands()()
    });


    function doc_keyUp(e) {
        if (e.key === 'j' && e.metaKey) {
            eel.playAssistantSound()
            $("#Oval").attr("hidden", true);
            $("#SiriWave").attr("hidden", false);
            eel.allCommands()()
        }
    }
    document.addEventListener('keyup', doc_keyUp, false);

    // to play assistant 
    function PlayAssistant(message) {
        if (message.trim() !== "") {
            $("#Oval").attr("hidden", true);
            $("#SiriWave").attr("hidden", false);
            
            eel.textCommand(message)(); 
            
            $("#chatbox").val("");
            $("#MicBtn").attr('hidden', false);
            $("#SendBtn").attr('hidden', true);
        }
    }

    // toggle function to hide and display mic and send button 
    function ShowHideButton(message) {
        if (message.length == 0) {
            $("#MicBtn").attr('hidden', false);
            $("#SendBtn").attr('hidden', true);
        }
        else {
            $("#MicBtn").attr('hidden', true);
            $("#SendBtn").attr('hidden', false);
        }
    }

    // key up event handler on text box
    $("#chatbox").keyup(function () {
        let message = $("#chatbox").val();
        ShowHideButton(message)
    });

    // send button event handler
    $("#SendBtn").click(function () {
        let message = $("#chatbox").val()
        PlayAssistant(message)
    });


    // enter press event handler on chat box
    $("#chatbox").keypress(function (e) {
        key = e.which;
        if (key == 13) {
            let message = $("#chatbox").val()
            PlayAssistant(message)
        }
    });


    // Settings Code: UPDATED NAMES TO PREVENT FREEZING
    eel.personalInfo()();
    eel.fetchSysCommand()();
    eel.fetchWebCommand()();
    eel.fetchPhoneBook()();



    // Execute: python side :
    eel.expose(getData)
    function getData(user_info) {
        let data = JSON.parse(user_info);
        let idsPersonalInfo = ['OwnerName', 'Designation', 'MobileNo', 'Email', 'City']
        let idsInputInfo = ['InputOwnerName', 'InputDesignation', 'InputMobileNo', 'InputEmail', 'InputCity']

        for (let i = 0; i < data.length; i++) {
            hashid = "#" + idsPersonalInfo[i]
            $(hashid).text(data[i]);
            $("#" + idsInputInfo[i]).val(data[i]);
        }

    }

    // Personal Data Update Button:
    $("#UpdateBtn").click(function () {

        let OwnerName = $("#InputOwnerName").val();
        let Designation = $("#InputDesignation").val();
        let MobileNo = $("#InputMobileNo").val();
        let Email = $("#InputEmail").val();
        let City = $("#InputCity").val();

        if (OwnerName.length > 0 && Designation.length > 0 && MobileNo.length > 0 && Email.length > 0 && City.length > 0) {
            eel.updatePersonalInfo(OwnerName, Designation, MobileNo, Email, City)

            swal({
                title: "Updated Successfully",
                icon: "success",
            });


        }
        else {
            const toastLiveExample = document.getElementById('liveToast')
            const toast = new bootstrap.Toast(toastLiveExample)

            $("#ToastMessage").text("All Fields Mandatory");

            toast.show()
        }

    });


    // Display System Command Method
    eel.expose(displaySysCommand)
    function displaySysCommand(array) {

        let data = JSON.parse(array);
        let placeholder = document.querySelector("#TableData");
        let out = "";
        let index = 0
        for (let i = 0; i < data.length; i++) {
            index++
            out += `
                    <tr>
                        <td class="text-light"> ${index} </td>
                        <td class="text-light"> ${data[i][1]} </td>
                        <td class="text-light"> ${data[i][2]} </td>
                        <td class="text-light"> <button id="${data[i][0]}" onClick="SysDeleteID(this.id)" class="btn btn-sm btn-glow-red">Delete</button></td>
                    </tr>
            `;
        }
        placeholder.innerHTML = out;
    }

    // Add System Command Button
    $("#SysCommandAddBtn").click(function () {

        let key = $("#SysCommandKey").val();
        let value = $("#SysCommandValue").val();

        if (key.length > 0 && value.length) {
            eel.addSysCommand(key, value)

            swal({
                title: "Updated Successfully",
                icon: "success",
            });
            eel.fetchSysCommand()(); // UPDATED NAME
            $("#SysCommandKey").val("");
            $("#SysCommandValue").val("");
        }
        else {
            const toastLiveExample = document.getElementById('liveToast')
            const toast = new bootstrap.Toast(toastLiveExample)
            $("#ToastMessage").text("All Fields Mandatory");
            toast.show()
        }

    });


    // Display Web Commands Table
    eel.expose(displayWebCommand)
    function displayWebCommand(array) {

        let data = JSON.parse(array);
        let placeholder = document.querySelector("#WebTableData");
        let out = "";
        let index = 0
        for (let i = 0; i < data.length; i++) {
            index++
            out += `
                    <tr>
                        <td class="text-light"> ${index} </td>
                        <td class="text-light"> ${data[i][1]} </td>
                        <td class="text-light"> ${data[i][2]} </td>
                        <td class="text-light"> <button id="${data[i][0]}" onClick="WebDeleteID(this.id)" class="btn btn-sm btn-glow-red">Delete</button></td>
                    </tr>
            `;
        }
        placeholder.innerHTML = out;
    }


    // Add Web Commands
    $("#WebCommandAddBtn").click(function () {

        let key = $("#WebCommandKey").val();
        let value = $("#WebCommandValue").val();

        if (key.length > 0 && value.length) {
            eel.addWebCommand(key, value)

            swal({
                title: "Updated Successfully",
                icon: "success",
            });
            eel.fetchWebCommand()(); // UPDATED NAME
            $("#WebCommandKey").val("");
            $("#WebCommandValue").val("");
        }
        else {
            const toastLiveExample = document.getElementById('liveToast')
            const toast = new bootstrap.Toast(toastLiveExample)
            $("#ToastMessage").text("All Fields Mandatory");
            toast.show()
        }

    });


    // Display Phone Book
    eel.expose(displayPhoneBookCommand)
    function displayPhoneBookCommand(array) {

        let data = JSON.parse(array);
        let placeholder = document.querySelector("#ContactTableData");
        let out = "";
        let index = 0
        for (let i = 0; i < data.length; i++) {
            index++
            out += `
                    <tr>
                        <td class="text-light"> ${index} </td>
                        <td class="text-light"> ${data[i][1]} </td>
                        <td class="text-light"> ${data[i][2]} </td>
                        <td class="text-light"> ${data[i][3]} </td>
                        <td class="text-light"> ${data[i][4]} </td>
                        <td class="text-light"> <button id="${data[i][0]}" onClick="ContactDeleteID(this.id)" class="btn btn-sm btn-glow-red">Delete</button></td>
                    </tr>
            `;
        }
        placeholder.innerHTML = out;
    }

    // Add Contacts to database
    $("#AddContactBtn").click(function () {

        let Name = $("#InputContactName").val();
        let MobileNo = $("#InputContactMobileNo").val();
        let Email = $("#InputContactEmail").val();
        let City = $("#InputContactCity").val();

        if (Name.length > 0 && MobileNo.length > 0) {

            if (Email.length < 0) { Email = ""; }
            else if (City < 0) { City = ""; }

            eel.InsertContacts(Name, MobileNo, Email, City)

            swal({
                title: "Updated Successfully",
                icon: "success",
            });

            $("#InputContactName").val("");
            $("#InputContactMobileNo").val("");
            $("#InputContactEmail").val("");
            $("#InputContactCity").val("");
            eel.fetchPhoneBook()() // UPDATED NAME

        }
        else {
            const toastLiveExample = document.getElementById('liveToast')
            const toast = new bootstrap.Toast(toastLiveExample)
            $("#ToastMessage").text("Name and Mobile number Mandatory");
            toast.show()
        }

    });

});

// DELETE FUNCTIONS - ALL UPDATED TO USE NEW NAMES
function SysDeleteID(clicked_id) {
    eel.deleteSysCommand(clicked_id)
    eel.fetchSysCommand()();
}

function WebDeleteID(clicked_id) {
    eel.deleteWebCommand(clicked_id)
    eel.fetchWebCommand()();
}

function ContactDeleteID(clicked_id) {
    eel.deletePhoneBookCommand(clicked_id)
    eel.fetchPhoneBook()();
}