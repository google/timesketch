import {Component, Input} from '@angular/core'

@Component({
  selector: 'ts-navigation',
  templateUrl: './navigation.ng.html',
})
export class NavigationComponent {
  @Input() sketchId: number
  @Input() active: string
}
