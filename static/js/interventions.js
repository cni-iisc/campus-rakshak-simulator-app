//Key-value store to map intervention text to code
var intv_code = {
    "0": "No Intervention (business as usual)",
    "1": "Case Isolation",
    "2": "Class Isolation ",
    "3": "Shelter in Place (no activity allowed)",
    "4": "Campus Evacuation",
    "5": "Custom intervention"
};

//Key-value store to map code to the intervention definiton in the simulator
var intv_sim_map = {
    "0": "no_intervention",
    "1": "case_isolation",
    "2": "class_isolation",
    "3": "lockdown",
    "4": "evacuation",
    "5": "selective_shutdown"
};


// This is populated based on the interaction space codes in simulator/cpp-simulator/models.h
var interaction_space_map = {
    // "0": "No Off-campus visitors",
    "1": "No Classes",
    "2": "Stay within Hostels",
    "3": "Close Messes",
    "4": "Close Cafeterias",
    "5": "Close Library",
    "6": "Close Sports&Gym",
    "7": "Close Rec. Spaces",
    "8": "Stay at Home",
    // "9": "Stay at Houses",
    // "10": "Small Networks",
    // "11": "Count"
};

var count = 0;

//function to layout the elements of an intervention block
function makeInterventionLayout(count, elemId, values={}){
    var li = $('<li>', {
        id: count,
        'class': 'interv-li'
    });

    //Divs for holding the
    var liDiv = $('<div>', {
        'class': 'li-interv-div row'
    });
    var col1 = $('<div>', {
        'class': 'col-5'
    });
    var col2 = $('<div>', {
        'class': 'col-2'
    });
    var col3 = $('<div>', {
        'class': 'col-5'
    });

    //Multiselect with interventions
    const createOption = (value, text) => {
        return  $("<option>").text(text).val(value);
    };

    $('<label>', {
        'for':'spaceList'+elemId
    }).text("Select the interaction spaces to disable").appendTo(spaceDiv)

    var select = $('<select>', {
        id: "mulIntv"+elemId,
        'class': "li-interv-select",
        'multiple': true,
    });

    for (let code in intv_code) {
        select.append(createOption(code, intv_code[code]))
    }

    //TODO: if values['intervention'].length > 0
    //TODO: set the select interventions as either value if length == 1 else set the selected attribute as true if the number of interventions is more than 1
    // if(values['intervention'].length > 0){
    //     if (values['intervention'].length > 1){
    //         for(var e in values['intervention']){
    //             select.options[values['intervention'][e]].selected = true
    //         }
    //     }
    //     else{
    //         select.value = values['intervention']
    //     }
    // }
    // else{
    //     select.value = 0
    // }

    //Compliance probability input
    $("<label>", {
        'for': "compProb"+elemId,
    }).text("Compliance Proabability").appendTo(col3);
    $("<input>", {
        id: "compProb"+elemId,
        'class': 'li-interv-time',
        'min': '0',
        'max': '1',
        'value': values['compliance'] ? values['compliance'] : null,
        'step': '0.001',
        'type': 'number'
    }).appendTo(col3);

    //Format the col-3
    $('<br><br>').appendTo(col3)

    //Number of days when the intervention block is active
    $("<label>", {
        'for': "numDays"+elemId,
    }).text("Duration of intervention block (days)").appendTo(col3);
    $("<input>", {
        id: "numDays"+elemId,
        'class': 'li-interv-time',
        'min': 1,
        'step': 1,
        'value': values['num_days'] ? values['num_days'] : null,
        'type': 'number'
    }).appendTo(col3);


    //Add the button to delete the intervention bloc to col-3
    $("<button>", {
        'html': '<i class="fas fa-2x fa-times-circle"></i>Delete Block',
        'class': 'btn btn-sm btn-danger',
        'on' : {
            click: function(){
                $(this).parent().parent().remove();
            }
        }
    }).appendTo(col3);

    //make a div of checkboxes for the interaction space
    var spaceDiv = $('<div>', {
        id:"spaceDiv"+elemId,
    });
    spaceDiv.hide()

    $('<label>', {
        'for':'spaceList'+elemId
    }).text("Select the interaction spaces to disable").appendTo(spaceDiv)

    var spaceList = $('<ul>', {
        id: 'spaceList'+elemId,
        'class': 'checkboxes'
    })

    //make the checboxes for each interaction space
    const createCheckbox = (value, text) => {
        var spaceli = $('<li>')
        $('<input>', {
            id:"space" + value,
            'type': 'checkbox',
            'value': value,
            'name': 'interaction_space_box',
        }).appendTo(spaceli)

        $("<label>", {
            'for': "space" + String(value),
        }).text(text).appendTo(spaceli);

        return spaceli
    };

    for (code in interaction_space_map){
        spaceList.append(createCheckbox(code, interaction_space_map[code]))
    }

    spaceList.appendTo(spaceDiv)
    select.appendTo(col1)
    spaceDiv.appendTo(col1)
    col1.appendTo(liDiv)
    col2.appendTo(liDiv)
    col3.appendTo(liDiv)
    $('<hr>').appendTo(liDiv)
    liDiv.appendTo(li)
    return li
}


//create new intervention -- for create view
function newInterv(elemId){

    var li = makeInterventionLayout(count, elemId)
    $("#interv").append(li);

    count++;
    elemId++;
    return elemId
}

//populate existing interventions -- for update view
function existingInterv(jsonElem, jsonId, elemId){
    var valDict = {}
    valDict['num_days'] = jsonElem['num_days']
    valDict['compliance'] = jsonElem['compliance']

    var jsonKeys = []
    for(var k in jsonElem){
        for( var intElem in intv_sim_map){
            if (intv_sim_map[intElem] == k & ((k != 'num_days') || (k != 'compliance'))){
                console.log(k)
                jsonKeys.push(intElem)
            }
        }
    }
    valDict['intervention'] = jsonKeys

    //TODO: support the interaction spaces that were disabled

     count++;
     elemId++;
     return elemId;
}

// make the intervention json by combining the intervention blocks
function intervention_json_gen(intv, complaince_probability, num_days, spaces) {
    var intv_list = []
    for (var j = 0; j < intv.length; j++) {
        var intv_json_const = {}
        intv_json_const["num_days"] = parseInt(num_days[j]);
        intv_json_const["compliance"] = parseFloat(complaince_probability[j]);
        for (var i = 0; i < intv[j].length; i++) {
            switch(intv[j][i]) {
                case 0 :
                    break;
                default :
                    if (intv[j][i] > 0){
                        if (intv[j][i] == 5){
                            console.log(spaces[j])
                            intv_json_const[[intv_sim_map[String(intv[j][i])]]] = {
                                "active" : true,
                                "spaces": []
                            }
                            for(e in spaces[j]){
                                intv_json_const[[intv_sim_map[String(intv[j][i])]]]['spaces'].push(parseInt(spaces[j][e]));
                            }


                        }
                        else{
                            intv_json_const[[intv_sim_map[String(intv[j][i])]]] = {
                                "active" : true
                            }
                        }
                    }
            }
        }
        intv_list.push(intv_json_const);
    }
    console.log(intv_list);
    return intv_list;
}
