odoo.define('web_studio.tests.tour', function (require) {
"use strict";

const tour = require('web_tour.tour');

const { randomString } = require('web_studio.utils');

let createdAppString = null;
let createdMenuString = null;

tour.register('web_studio_tests_tour', {
    test: true,
    url: "/web?debug=tests",
}, [{
    // open studio
    trigger: '.o_main_navbar .o_web_studio_navbar_item',
}, {
    trigger: '.o_web_studio_new_app',
}, {
    // the next steps are here to create a new app
    trigger: '.o_web_studio_app_creator_next',
}, {
    trigger: '.o_web_studio_app_creator_name > input',
    run: 'text ' + (createdAppString = randomString(6)),
}, {
    trigger: '.o_web_studio_app_creator_next.is_ready',
}, {
    trigger: '.o_web_studio_app_creator_menu > input',
    run: 'text ' + (createdMenuString = randomString(6)),
}, {
    trigger: '.o_web_studio_app_creator_next.is_ready',
}, {
    // disable chatter in model configurator, we'll test adding it on later
    trigger: 'input[name="use_mail"]',
}, {
    // disable company if visible, otherwise it might make the test uncertain
    trigger: 'body',
    run: () => {
        const $input = $('input[name="use_company"]');
        if ($input) {
            $input.click();
        }
    }
}, {
    trigger: '.o_web_studio_model_configurator_next',
}, {
    // toggle the home menu outside of studio and come back in studio
    extra_trigger: '.o_menu_toggle.fa-th',
    trigger: '.o_web_studio_leave',
    timeout: 60000, /* previous step reloads registry, etc. - could take a long time */
}, {
    extra_trigger: `.o_web_client:not(.o_in_studio)`,  /* wait to be out of studio */
    trigger: '.o_menu_toggle.fa-th',
    timeout: 60000, /* previous step reloads registry, etc. - could take a long time */
}, {
    trigger: '.o_main_navbar .o_web_studio_navbar_item',
}, {
    // open the app creator and leave it
    trigger: '.o_web_studio_new_app',
}, {
    extra_trigger: '.o_web_studio_app_creator',
    trigger: '.o_web_studio_leave',
}, {
    // go back to the previous app
    trigger: '.o_home_menu',
    run: () => {
        window.dispatchEvent(new KeyboardEvent('keydown', {
            bubbles: true,
            key: 'Escape',
        }));
    },
}, {
    // this should open the previous app outside of studio
    extra_trigger: `.o_web_client:not(.o_in_studio) .o_menu_brand:contains(${createdAppString})`,
    // go back to the home menu
    trigger: '.o_menu_toggle.fa-th',
}, {
    // check that the menu exists
    trigger: 'input.o_menu_search_input',
    run: 'text ' + createdMenuString,
}, {
    // search results should have been updated
    extra_trigger: `.o_menuitem.o_focused:contains(${createdAppString} / ${createdMenuString})`,
    // enter Studio
    trigger: '.o_main_navbar .o_web_studio_navbar_item',
}, {
    // edit an app
    trigger: `.o_app[data-menu-xmlid*="studio"]:contains(${createdAppString})`,
    run: function () {
        // We can't emulate a hover to display the edit icon
        const editIcon = this.$anchor[0].querySelector('.o_web_studio_edit_icon');
        editIcon.style.visibility = 'visible';
        editIcon.click();
    },
}, {
    // design the icon
    // TODO: we initially tested this (change an app icon) at the end but a
    // long-standing bug (KeyError: ir.ui.menu.display_name, caused by a registry
    // issue with multiple workers) on runbot prevent us from doing it. It thus have
    // been moved at the beginning of this test to avoid the registry to be reloaded
    // before the write on ir.ui.menu.
    trigger: '.o_web_studio_selector:eq(0)',
}, {
    trigger: '.o_web_studio_palette > .o_web_studio_selector:first',
}, {
    trigger: '.modal-footer .btn.btn-primary',
}, {
    // click on the created app
    trigger: `.o_app[data-menu-xmlid*="studio"]:contains(${createdAppString})`,
}, {
    // create a new menu
    trigger: '.o_main_navbar .o_web_edit_menu',
}, {
    trigger: 'footer.modal-footer .js_add_menu',
}, {
    trigger: 'input[name="name"]',
    run: 'text ' + (createdMenuString = randomString(6)),
}, {
    trigger: 'div[name="model_choice"] input[data-value="existing"]',
}, {
    trigger: '.o_field_many2one[name="model"] input',
    run: 'text a',
}, {
    trigger: '.ui-autocomplete > .ui-menu-item:first > a',
    in_modal: false,
}, {
    trigger: 'button:contains(Confirm):not(".disabled")',
}, {
    trigger: 'button:contains(Confirm):not(".disabled")',
}, {
    // check that the Studio menu is still there
    extra_trigger: '.o_web_studio_menu',
    // switch to form view
    trigger: '.o_web_studio_views_icons > a[data-name="form"]',
}, {
    // wait for the form editor to be rendered because the sidebar is the same
    extra_trigger: '.o_web_studio_form_view_editor',
    // add an existing field (display_name)
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_char',
    run: 'drag_and_drop .o_web_studio_form_view_editor .o_inner_group',
}, {
    // click on the field
    trigger: '.o_web_studio_form_view_editor td.o_td_label:first',
    // when it's there
    extra_trigger: 'input[data-type="field_name"]',
}, {
    // rename the label
    trigger: '.o_web_studio_sidebar_content.o_display_field input[name="string"]',
    run: 'text My Coucou Field',
}, {
    // verify that the field name has changed and change it
    trigger: 'input[data-type="field_name"][value="my_coucou_field"]',
    run: 'text coucou',
}, {
    // click on "Add" tab
    trigger: '.o_web_studio_sidebar .o_web_studio_new',
}, {
    // add a new field
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_char',
    run: 'drag_and_drop .o_web_studio_form_view_editor .o_inner_group',
}, {
    // rename the field with the same name
    trigger: 'input[data-type="field_name"]',
    run: 'text coucou',
}, {
    // an alert dialog should be opened
    trigger: '.modal-footer > button:first',
}, {
    // rename the label
    trigger: '.o_web_studio_sidebar_content.o_display_field input[name="string"]',
    run: 'text COUCOU',
}, {
    // verify that the field name has changed (post-fixed by _1)
    extra_trigger: 'input[data-type="field_name"][value="coucou_1"]',
    trigger: '.o_web_studio_sidebar .o_web_studio_new',
}, {
    // add a monetary field --> create a currency field
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_monetary',
    run: 'drag_and_drop .o_web_studio_form_view_editor .o_inner_group',
}, {
    trigger: '.modal-footer .btn.btn-primary',
}, {
    // verify that the currency field is in the view
    extra_trigger: '.o_web_studio_form_view_editor td.o_td_label:contains("Currency")',
    trigger: '.o_web_studio_sidebar .o_web_studio_new',
}, {
    // add a monetary field
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_monetary',
    run: 'drag_and_drop (.o_web_studio_form_view_editor .o_inner_group:first .o_web_studio_hook:eq(1))',
}, {
    // verify that the monetary field is in the view
    extra_trigger: '.o_web_studio_form_view_editor td.o_td_label:eq(1):contains("New Monetary")',
    // switch the two first fields
    trigger: '.o_web_studio_form_view_editor .o_inner_group:first .ui-draggable:eq(1)',
    run: 'drag_and_drop .o_inner_group:first .o_web_studio_hook:first',
}, {
    // click on "Add" tab
    trigger: '.o_web_studio_sidebar .o_web_studio_new',
}, {
    // verify that the fields have been switched
    extra_trigger: '.o_web_studio_form_view_editor td.o_td_label:eq(0):contains("New Monetary")',
    // add a m2m field
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_many2many',
    run: 'drag_and_drop .o_inner_group:first .o_web_studio_hook:first',
}, {
    // type something in the modal
    trigger: '.o_field_many2one[name="model"] input',
    run: 'text a',
}, {
    // select the first model
    trigger: '.ui-autocomplete > .ui-menu-item:first > a',
    in_modal: false,
}, {
    trigger: 'button:contains(Confirm)',
}, {
    // select the m2m to set its properties
    trigger: 'tr:has(.o_field_many2many)',
    timeout: 15000,  // creating M2M relations can take some time...
}, {
    // change the `widget` attribute
    trigger: '.o_web_studio_sidebar select[name="widget"]',
    run: function () {
        this.$anchor.val('many2many_tags').trigger('change');
    },
}, {
    // use colors on the m2m tags
    trigger: '.o_web_studio_sidebar label[for="option_color_field"]',
}, {
    // add a statusbar
    trigger: '.o_web_studio_statusbar_hook',
}, {
    trigger: '.modal-footer .btn.btn-primary',
}, {
    trigger: '.o_statusbar_status',
}, {
    // verify that a default value has been set for the statusbar
    trigger: '.o_web_studio_sidebar select[name="default_value"]:contains(First Status)',
}, {
    trigger: '.o_web_studio_views_icons a[data-name=form]',
}, {
    // verify Chatter can be added after changing view to form
    extra_trigger: '.o_web_studio_add_chatter',
    // edit action
    trigger: '.o_web_studio_menu .o_menu_sections li[data-name="views"]',
}, {
    // edit form view
    trigger: '.o_web_studio_view_category .o_web_studio_view_type[data-type="form"] .o_web_studio_thumbnail',
}, {
    // verify Chatter can be added after changing view to form
    extra_trigger: '.o_web_studio_add_chatter',
    // switch in list view
    trigger: '.o_web_studio_menu .o_web_studio_views_icons a[data-name="list"]',
}, {
    // wait for the list editor to be rendered because the sidebar is the same
    extra_trigger: '.o_web_studio_list_view_editor',
    // add an existing field (display_name)
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_char',
    run: 'drag_and_drop .o_web_studio_list_view_editor th.o_web_studio_hook:first',
}, {
    // verify that the field is correctly named
    extra_trigger: '.o_web_studio_list_view_editor th:contains("COUCOU")',
    // leave Studio
    trigger: '.o_web_studio_leave',
}, {
    // come back to the home menu to check if the menu data have changed
    extra_trigger: '.o_web_client:not(.o_in_studio)',
    trigger: '.o_menu_toggle.fa-th',
}, {
    trigger: 'input.o_menu_search_input',
    run: 'text ' + createdMenuString,
}, {
    // search results should have been updated
    extra_trigger: `.o_menuitem.o_focused:contains(${createdAppString} / ${createdMenuString})`,
    // cleans the search bar query
    trigger: '.o_home_menu',
    run: () => {
        window.dispatchEvent(new KeyboardEvent('keydown', {
            bubbles: true,
            key: 'Escape',
        }));
    },
}, {
    // go back again to the app (using keyboard)
    trigger: '.o_home_menu',
    run: () => {
        window.dispatchEvent(new KeyboardEvent('keydown', {
            bubbles: true,
            key: 'Escape',
        }));
    },
}, {
    // re-open studio
    trigger: '.o_web_studio_navbar_item',
}, {
    // modify the list view
    trigger: '.o_web_studio_sidebar .o_web_studio_view'
}, {
    //select field you want to sort and based on that sorting will be applied on List view
    trigger: '.o_web_studio_sidebar .o_web_studio_sidebar_select #sort_field',
    run: function () {
        $('#sort_field option:eq(1)').attr('selected', 'selected');
        $('#sort_field option:eq(1)').change();
    }
}, {
    //change order of sorting, Select order and change it
    trigger: '.o_web_studio_sidebar .o_web_studio_sidebar_select #sort_order',
    run: function () {
        $('#sort_order option:eq(1)').attr('selected', 'selected');
        $('#sort_order option:eq(1)').change();
    }
}, {
    // edit action
    trigger: '.o_web_studio_menu .o_menu_sections li[data-name="views"]',
}, {
    // add a kanban
    trigger: '.o_web_studio_view_category .o_web_studio_view_type.o_web_studio_inactive[data-type="kanban"] .o_web_studio_thumbnail',
}, {
    // add a dropdown
    trigger: '.o_dropdown_kanban.o_web_studio_add_dropdown',
}, {
    trigger: '.modal-footer .btn.btn-primary',
}, {
    // select the dropdown for edition
    trigger: '.o_dropdown_kanban:not(.o_web_studio_add_dropdown)',
}, {
    // enable "Set Cover" feature
    trigger: '.o_web_studio_sidebar input[name=set_cover]',
}, {
    trigger: '.modal-footer .btn.btn-primary',
}, {
    // edit action
    trigger: '.o_web_studio_menu .o_menu_sections li[data-name="views"]',
}, {
    // check that the kanban view is now active
    extra_trigger: '.o_web_studio_view_category .o_web_studio_view_type:not(.o_web_studio_inactive)[data-type="kanban"]',
    // add an activity view
    trigger: '.o_web_studio_view_category .o_web_studio_view_type.o_web_studio_inactive[data-type="activity"] .o_web_studio_thumbnail',
}, {
    extra_trigger: '.o_activity_view',
    // edit action
    trigger: '.o_web_studio_menu .o_menu_sections li[data-name="views"]',
}, {
    // add a graph view
    trigger: '.o_web_studio_view_category .o_web_studio_view_type.o_web_studio_inactive[data-type="graph"] .o_web_studio_thumbnail',
}, {
    extra_trigger: '.o_graph_renderer',
    trigger: '.o_web_studio_menu .o_menu_sections li[data-name="views"]',
}, {
    extra_trigger: '.o_web_studio_views',
    // edit the search view
    trigger: '.o_web_studio_view_category .o_web_studio_view_type[data-type="search"] .o_web_studio_thumbnail',
}, {
    extra_trigger: '.o_web_studio_search_view_editor',
    trigger: '.o_menu_toggle.fa-th',
}, {
    trigger: '.o_web_studio_home_studio_menu .dropdown-toggle',
}, {
    // export all modifications
    trigger: '.o_web_studio_export',
}, {
    // click on the created app
    trigger: '.o_app[data-menu-xmlid*="studio"]:last',
}, {
    // switch to form view
    trigger: '.o_web_studio_views_icons > a[data-name="form"]',
}, {
    extra_trigger: '.o_web_studio_form_view_editor',
    // click on the view tab
    trigger: '.o_web_studio_view',
}, {
    // click on the restore default view button
    trigger: '.o_web_studio_restore',
}, {
    // click on the ok button
    trigger: '.modal-footer .btn.btn-primary',
}, {
    // checks that the field doesn't exist anymore
    extra_trigger: 'label.o_form_label:not(:contains("COUCOU"))',
    trigger: '.o_web_studio_leave'
}]);

tour.register('web_studio_hide_fields_tour', {
    url: "/web?studio=app_creator&debug=tests",
}, [{
    trigger: '.o_web_studio_new_app',
}, {
    trigger: '.o_web_studio_app_creator_next',
}, {
    trigger: `
        .o_web_studio_app_creator_name
        > input`,
    run: `text ${randomString(6)}`,
}, {
    // make another interaction to show "next" button
    trigger: `
        .o_web_studio_selectors
        .o_web_studio_selector:eq(2)`,
}, {
    trigger: '.o_web_studio_app_creator_next',
}, {
    trigger: `
        .o_web_studio_app_creator_menu
        > input`,
    run: `text ${randomString(6)}`,
}, {
    trigger: '.o_web_studio_app_creator_next',
}, {
    trigger: '.o_web_studio_model_configurator_next',
}, {
    // check that the Studio menu is still there
    extra_trigger: '.o_web_studio_menu',
    trigger: '.o_web_studio_leave',
    timeout: 60000, /* previous step reloads registry, etc. - could take a long time */
}, {
    trigger: '.oe_title input',
    run: 'text Test',
}, {
    trigger: '.o_form_button_save',
}, {
    trigger: '.o_web_studio_navbar_item',
}, {
    extra_trigger: '.o_web_studio_menu',
    trigger: `
        .o_web_studio_views_icons
        > a[data-name="list"]`,
}, {
    // wait for the list editor to be rendered because the sidebar is the same
    extra_trigger: '.o_web_studio_list_view_editor',
    trigger: `
        .o_web_studio_sidebar
        .o_web_studio_existing_fields
        .o_web_studio_component:has(.o_web_studio_component_description:contains(display_name))`,
    run: 'drag_and_drop .o_web_studio_list_view_editor .o_web_studio_hook',
}, {
    trigger: `
        .o_list_table
        th[data-name="display_name"]`,
}, {
    trigger: `
        .o_web_studio_sidebar
        select[name="optional"]`,
    run: "text Hide by default",
}, {
    extra_trigger: '.o_list_table:not(:has(th[data-name="display_name"]))',
    trigger: `
        .o_web_studio_sidebar_header
        .o_web_studio_view`,
}, {
    trigger: `
        .o_web_studio_sidebar_checkbox
        input#show_invisible`,
}, {
    extra_trigger: `
        .o_list_table
        th[data-name="display_name"].o_web_studio_show_invisible`,
    trigger: '.o_web_studio_leave',
}]);

tour.register('web_studio_new_report_tour', {
    url: "/web",
    test: true,
}, [{
    // open studio
    trigger: '.o_main_navbar .o_web_studio_navbar_item',
}, {
    // click on the created app
    trigger: '.o_app[data-menu-xmlid*="studio"]:first',
    extra_trigger: 'body.o_in_studio',
}, {
    // edit reports
    trigger: '.o_web_studio_menu li[data-name="reports"]',
}, {
    // create a new report
    trigger: '.o_control_panel .o-kanban-button-new',
}, {
    // select external layout
    trigger: '.o_web_studio_report_layout_dialog div[data-layout="web.external_layout"]',
}, {
    // sidebar should display add tab
    extra_trigger: '.o_web_studio_report_editor_manager .o_web_studio_sidebar_header div.active[name="new"]',
    // switch to 'Report' tab
    trigger: '.o_web_studio_report_editor_manager .o_web_studio_sidebar_header div[name="report"]',
}, {
    // edit report name
    trigger: '.o_web_studio_sidebar input[name="name"]',
    run: 'text My Awesome Report',
}, {
    // switch to 'Add' in Sidebar
    extra_trigger: '.o_web_studio_sidebar input[name="name"][value="My Awesome Report"]',
    trigger: '.o_web_studio_sidebar div[name="new"]',
}, {
    // wait for the iframe to be loaded
    extra_trigger: '.o_web_studio_report_editor iframe #wrapwrap',
    // add a 'title' building block
    trigger: '.o_web_studio_sidebar .o_web_studio_component:contains(Title Block)',
    run: 'drag_and_drop .o_web_studio_report_editor iframe .article > .page',
    auto: true,
}, {
    // click on the newly added field
    trigger: '.o_web_studio_report_editor iframe .h2 > span:contains(New Title)',
}, {
    // change the text of the H2 to 'test'
    trigger: '.o_web_studio_sidebar .o_web_studio_text .note-editable',
    run: function () {
        this.$anchor.focusIn();
        this.$anchor[0].firstChild.textContent = 'Test';
        this.$anchor.keydown();
        this.$anchor.blur();
    }
}, {
    // click outside to blur the field
    trigger: '.o_web_studio_report_editor',
    extra_trigger: '.o_web_studio_sidebar .o_web_studio_text .note-editable:contains(Test)',
}, {
    extra_trigger: '.o_web_studio_report_editor iframe .h2:contains(Test)',
    // add a new group on the node
    trigger: '.o_web_studio_sidebar .o_field_many2manytags[name="groups"] input',
    run: function () {
        this.$anchor.click();
    },
}, {
    trigger: '.ui-autocomplete:visible li:contains(Access Rights)',
}, {
    // wait for the group to appear
    extra_trigger: '.o_web_studio_sidebar .o_field_many2manytags[name="groups"] .o_badge_text:contains(Access Rights)',
    // switch to 'Add' in Sidebar
    trigger: '.o_web_studio_sidebar div[name="new"]',
}, {
    // add a 'title' building block Data Table
    trigger: '.o_web_studio_sidebar .o_web_studio_component:contains(Data table)',
    run: 'drag_and_drop .o_web_studio_report_editor iframe .article > .page',
}, {
    // expand the model selector in the popup
    trigger: 'div.o_field_selector_value',
    run: function () {
        $('div.o_field_selector_value').focusin();
    }
}, {
    // select the second element of the model (followers)
    trigger: '.o_field_selector_popover_body > ul > li:contains(Followers)'
}, {
    trigger:'.modal-content button>span:contains(Confirm)', // button
    extra_trigger:'.o_field_selector_chain_part:contains(Followers)',//content of the field is set
}, {
    // select the content of the first field of the newly added table
    trigger: '.o_web_studio_report_editor iframe span[t-field="table_line.display_name"]'
}, {
    // change the bound field
    trigger: '.o_web_studio_sidebar .card:last() div.o_field_selector_value',
    run: function () {
        $('.o_web_studio_sidebar .card:last() div.o_field_selector_value').focusin();
    }
}, {
    trigger: 'ul.o_field_selector_page li:contains(ID)'
}, {
    // update the title of the column
    extra_trigger: '.o_web_studio_report_editor iframe span[t-field="table_line.id"]',
    trigger: '.o_web_studio_report_editor iframe table thead span:contains(Name) ', // the name title
    //extra_trigger: '.o_web_studio_report_editor iframe span[t-field="table_line.display_name"]:not(:contains(YourCompany, Administrator))', // the id has been updated in the iframe
}, {
    // update column title 'name' into another title
    trigger: '.o_web_studio_sidebar .o_web_studio_text .note-editable',
        run: function () {
        this.$anchor.focusIn();
        this.$anchor[0].firstChild.textContent = 'new column title';
        this.$anchor.keydown();
        this.$anchor.blur();
    }
}, {
    // click outside to blur the field
    trigger: '.o_web_studio_report_editor',
    extra_trigger: '.o_web_studio_sidebar .o_web_studio_text .note-editable:contains(new column title)',
}, {
    // wait to be sure the modification has been correctly applied
    extra_trigger: '.o_web_studio_report_editor iframe table thead span:contains(new column title) ',
    // leave the report
    trigger: '.o_web_studio_breadcrumb .o_back_button:contains(Reports)',
}, {
    // a invisible element cannot be used as a trigger so this small hack is
    // mandatory for the next step
    run: function () {
        $('.o_kanban_record:contains(My Awesome Report) .o_dropdown_kanban').css('visibility', 'visible');
    },
    trigger: '.o_kanban_view',
}, {
    // open the dropdown
    trigger: '.o_kanban_record:contains(My Awesome Report) .dropdown-toggle',
}, {
    // duplicate the report
    trigger: '.o_kanban_record:contains(My Awesome Report) .dropdown-menu a:contains(Duplicate)',
}, {
    // open the duplicate report
    trigger: '.o_kanban_record:contains(My Awesome Report copy(1))',
}, {
    // switch to 'Report' tab
    trigger: '.o_web_studio_report_editor_manager .o_web_studio_sidebar_header div[name="report"]',
}, {
    // wait for the duplicated report to be correctly loaded
    extra_trigger: '.o_web_studio_sidebar input[name="name"][value="My Awesome Report copy(1)"]',
    // leave Studio
    trigger: '.o_web_studio_leave',
}]);

tour.register('web_studio_new_report_basic_layout_tour', {
    url: "/web",
    test: true,
}, [{
    // open studio
    trigger: '.o_main_navbar .o_web_studio_navbar_item',
}, {
    // click on the created app
    trigger: '.o_app[data-menu-xmlid*="studio"]:first',
    extra_trigger: 'body.o_in_studio',
}, {
    // edit reports
    trigger: '.o_web_studio_menu li[data-name="reports"]',
}, {
    // create a new report
    trigger: '.o_control_panel .o-kanban-button-new',
}, {
    // select external layout
    trigger: '.o_web_studio_report_layout_dialog div[data-layout="web.basic_layout"]',
}, {
    // sidebar should display add tab
    extra_trigger: '.o_web_studio_report_editor_manager .o_web_studio_sidebar_header div.active[name="new"]',
    // switch to 'Report' tab
    trigger: '.o_web_studio_report_editor_manager .o_web_studio_sidebar_header div[name="report"]',
}, {
    // edit report name
    trigger: '.o_web_studio_sidebar input[name="name"]',
    run: 'text My Awesome basic layout Report',
}, {
    // switch to 'Add' in Sidebar
    extra_trigger: '.o_web_studio_sidebar input[name="name"][value="My Awesome basic layout Report"]',
    trigger: '.o_web_studio_sidebar div[name="new"]',
}, {
    // wait for the iframe to be loaded
    extra_trigger: '.o_web_studio_report_editor iframe #wrapwrap',
    // add a 'title' building block
    trigger: '.o_web_studio_sidebar .o_web_studio_component:contains(Title Block)',
    run: 'drag_and_drop .o_web_studio_report_editor iframe .article > .page',
    auto: true,
}, {
    // click on the newly added field
    trigger: '.o_web_studio_report_editor iframe .h2 > span:contains(New Title)',
}, {
    // change the text of the H2 to 'test'
    trigger: '.o_web_studio_sidebar .o_web_studio_text .note-editable',
    run: function () {
        this.$anchor.focusIn();
        this.$anchor[0].firstChild.textContent = 'Test';
        this.$anchor.keydown();
        this.$anchor.blur();
    }
}, {
    // click outside to blur the field
    trigger: '.o_web_studio_report_editor',
    extra_trigger: '.o_web_studio_sidebar .o_web_studio_text .note-editable:contains(Test)',
}, {
    extra_trigger: '.o_web_studio_report_editor iframe .h2:contains(Test)',
    // add a new group on the node
    trigger: '.o_web_studio_sidebar .o_field_many2manytags[name="groups"] input',
    run: function () {
        this.$anchor.click();
    },
}, {
    trigger: '.ui-autocomplete:visible li:contains(Access Rights)',
}, {
    // wait for the group to appear
    extra_trigger: '.o_web_studio_sidebar .o_field_many2manytags[name="groups"] .o_badge_text:contains(Access Rights)',
    // switch to 'Add' in Sidebar
    trigger: '.o_web_studio_sidebar div[name="new"]',
}, {
    // add a 'title' building block Data Table
    trigger: '.o_web_studio_sidebar .o_web_studio_component:contains(Data table)',
    run: 'drag_and_drop .o_web_studio_report_editor iframe .article > .page',
}, {
    // expand the model selector in the popup
    trigger: 'div.o_field_selector_value',
    run: function () {
        $('div.o_field_selector_value').focusin();
    }
}, {
    // select the second element of the model (followers)
    trigger: '.o_field_selector_popover_body > ul > li:contains(Followers)'
}, {
    trigger:'.modal-content button>span:contains(Confirm)', // button
    extra_trigger:'.o_field_selector_chain_part:contains(Followers)', //content of the field is set
}, {
    // select the content of the first field of the newly added table
    trigger: '.o_web_studio_report_editor iframe span[t-field="table_line.display_name"]'
}, {
    // change the bound field
    trigger: '.o_web_studio_sidebar .card:last() div.o_field_selector_value',
    run: function () {
        $('.o_web_studio_sidebar .card:last() div.o_field_selector_value').focusin();
    }
}, {
    trigger: 'ul.o_field_selector_page li:contains(ID)'
}, {
    // update the title of the column
    trigger: '.o_web_studio_report_editor iframe table thead span:contains(Name) ', // the name title
    //extra_trigger: '.o_web_studio_report_editor iframe span[t-field="table_line.display_name"]:not(:contains(YourCompany, Administrator))', // the id has been updated in the iframe
}, {
    // update column title 'name' into another title
    trigger: '.o_web_studio_sidebar .o_web_studio_text .note-editable',
    run: function () {
        this.$anchor.focusIn();
        this.$anchor[0].firstChild.textContent = 'new column title';
        this.$anchor.keydown();
        this.$anchor.blur();
    }
}, {
    // click outside to blur the field
    trigger: '.o_web_studio_report_editor',
    extra_trigger: '.o_web_studio_sidebar .o_web_studio_text .note-editable:contains(new column title)',
}, {
    // wait to be sure the modification has been correctly applied
    extra_trigger: '.o_web_studio_report_editor iframe table thead span:contains(new column title) ',
    // leave the report
    trigger: '.o_web_studio_breadcrumb .o_back_button:contains(Reports)',
}, {
    // a invisible element cannot be used as a trigger so this small hack is
    // mandatory for the next step
    run: function () {
        $('.o_kanban_record:contains(My Awesome basic layout Report) .o_dropdown_kanban').css('visibility', 'visible');
    },
    trigger: '.o_kanban_view',
}, {
    // open the dropdown
    trigger: '.o_kanban_record:contains(My Awesome basic layout Report) .dropdown-toggle',
}, {
    // duplicate the report
    trigger: '.o_kanban_record:contains(My Awesome basic layout Report) .dropdown-menu a:contains(Duplicate)',
}, {
    // open the duplicate report
    trigger: '.o_kanban_record:contains(My Awesome basic layout Report copy(1))',
}, {
    // switch to 'Report' tab
    trigger: '.o_web_studio_report_editor_manager .o_web_studio_sidebar_header div[name="report"]',
}, {
    // wait for the duplicated report to be correctly loaded
    extra_trigger: '.o_web_studio_sidebar input[name="name"][value="My Awesome basic layout Report copy(1)"]',
    // leave Studio
    trigger: '.o_web_studio_leave',
}]);

tour.register('web_studio_approval_tour', {
    url: "/web",
    test: true,
}, [{
    // go to Apps menu
    trigger: '.o_app[data-menu-xmlid="base.menu_management"]',
}, {
    // open studio
    trigger: '.o_main_navbar .o_web_studio_navbar_item',
    extra_trigger: '.o_cp_switch_buttons',
}, {
    // switch to form view editor
    trigger: '.o_web_studio_views_icons a[data-name="form"]',
}, {
    // click on first button it finds that has a node id
    trigger: '.o_web_studio_form_view_editor button[data-node-id]',
}, {
    // enable approvals for the button
    trigger: '.o_web_studio_sidebar label[for="studio_approval"]',
}, {
    // set approval message
    trigger: '.o_web_studio_sidebar_approval input[name*="approval_message"]',
    run: 'text nope',
}, {
    // add approval rule
    trigger: '.o_web_studio_sidebar_approval .o_approval_new',
    extra_trigger: '.o_web_studio_snackbar .fa-check',
}, {
    // set domain on first rule
    trigger: '.o_web_studio_sidebar_approval .o_approval_domain',
    extra_trigger: '.o_studio_sidebar_approval_rule:eq(1)',
}, {
    // set stupid domain that is always truthy
    trigger: '.o_domain_debug_container input',
    run: function () {
        this.$anchor.focusIn();
        this.$anchor.val('[["id", "!=", False]]');
        this.$anchor.change();
    }
}, {
    // save domain and close modal
    trigger:' .modal-footer .btn-primary',
    extra_trigger: '.o_domain_leaf_edition',
}, {
    // add second approval rule when the first is set
    trigger: '.o_web_studio_sidebar_approval .o_approval_new',
    extra_trigger: '.o_web_studio_snackbar .fa-check',
}, {
    // enable 'force different users' for one rule (doesn't matter which)
    trigger: '.o_web_studio_sidebar label[for*="exclusive_user"]',
    extra_trigger: '.o_web_studio_snackbar .fa-check',
}, {
    // leave studio
    trigger: '.o_web_studio_leave',
    extra_trigger: '.o_web_studio_snackbar .fa-check',
}, {
    // go back to kanban
    trigger: '.o_menu_brand',
    extra_trigger: '.o_web_client:not(.o_in_studio)'
}, {
    // open first record (should be the one that was used, so the button should be there)
    trigger: '.o_kanban_view .o_kanban_record .o_dropdown_kanban .dropdown-toggle',
}, {
    trigger: '.dropdown-menu.show .dropdown-item',
},{
    // try to do the action
    trigger: 'button[studio_approval]',
}, {
    // there should be a warning
    trigger: '.o_notification.bg-warning'
}
]);

tour.register("web_studio_test_address_view_id_no_edit",
{
    url: "/web",
    test: true,
}, [{
    trigger: "a[data-menu-xmlid='web_studio.studio_test_partner_menu']"
},
{
    extra_trigger: ".o_form_view",
    trigger: ".o_address_format",
    run: function() {
        if (this.$anchor.find('[name=lang]').length || !this.$anchor.find('[name=street2]').length) {
            throw new Error("The address view id set on the company country should be displayed");
        };
    }
},
{
    trigger: ".o_web_studio_navbar_item a"
},
{
    extra_trigger: ".o_web_studio_view_renderer",
    trigger: ".o_address_format",
    run: function() {
        if (this.$anchor.find('[name=street2]').length || !this.$anchor.find('[name=lang]').length) {
            throw new Error("The address view id set on the company country shouldn't be editable");
        };
    }
},
{
    trigger: ".o_web_studio_leave"
}]);

});
