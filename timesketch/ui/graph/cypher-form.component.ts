import {
    Component,
    EventEmitter,
    Input,
    OnChanges,
    OnInit,
    Output, SimpleChanges
} from '@angular/core';
import { FormGroup, FormControl, Validators } from '@angular/forms';

@Component({
    selector: 'ts-cypher-form',
    templateUrl: './cypher-form.component.html'
})
export class CypherFormComponent implements OnInit, OnChanges {

    @Input() selectedQuery;
    @Output() cypherSearch = new EventEmitter<string>();

    form: FormGroup;
    formData;
    formDataIterable;
    queryData;

    constructor() {}
    ngOnInit() {}

    ngOnChanges(changes: SimpleChanges) {
        if (!this.selectedQuery) {
            return
        }

        this.formData = this.selectedQuery.form_data;

        this.formDataIterable = Object.keys(this.formData)
            .map(prop => {
                return Object.assign({}, { key: prop} , this.formData[prop]);
            });

        const formGroup = {};
        for(let prop of Object.keys(this.formData)) {
            formGroup[prop] = new FormControl(this.formData[prop].value || '');
        }
        this.form = new FormGroup(formGroup);
    }

    onSubmit(formResponse) {
        this.queryData = {
            id: this.selectedQuery.id,
            parameters: formResponse
        };
        this.cypherSearch.emit(this.queryData);
    }
}