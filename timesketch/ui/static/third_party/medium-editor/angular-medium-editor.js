/*global MediumEditor */
'use strict';

angular.module('angular-medium-editor', [])

  .directive('mediumEditor', function() {

    function toInnerText(value) {
      var tempEl = document.createElement('div'),
          text;
      tempEl.innerHTML = value;
      text = tempEl.textContent || '';
      return text.trim();
    }

    return {
      require: 'ngModel',
      restrict: 'AE',
      scope: { bindOptions: '=' },
      link: function(scope, iElement, iAttrs, ngModel) {

        angular.element(iElement).addClass('angular-medium-editor');

        // Global MediumEditor
        ngModel.editor = new MediumEditor(iElement, scope.bindOptions);

        ngModel.$render = function() {
          iElement.html(ngModel.$viewValue || "");
          ngModel.editor.getExtensionByName('placeholder').updatePlaceholder(iElement[0]);
        };

        ngModel.$isEmpty = function(value) {
          if (/[<>]/.test(value)) {
            return toInnerText(value).length === 0;
          } else if (value) {
            return value.length === 0;
          } else {
            return true;
          }
        };

        ngModel.editor.subscribe('editableInput', function (event, editable) {
            console.log(ngModel.editor.serialize());
            ngModel.$setViewValue(editable.innerHTML.trim());
        });

        scope.$watch('bindOptions', function(bindOptions) {
          ngModel.editor.init(iElement, bindOptions);
        });
      }
    };

  });
