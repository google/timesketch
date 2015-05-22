(function() {
    var module = angular.module('timesketch.core.butterbar.directive', []);

    module.directive("tsButterbar", function() {
        return {
            restrict : "A",
            link : function(scope, element, attrs) {
                scope.$on("httpreq-start", function(e) {
                    element.text("Loading..");
                    element.css({"display": "block"});
                });

                scope.$on("httpreq-error", function(e) {
                    element.css({"display": "block"});
                    element.text("Error")
                });

                scope.$on("httpreq-complete", function(e) {
                    element.css({"display": "none"});
                });
            }
        };
    });
})();

