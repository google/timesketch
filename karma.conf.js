// karma.conf.js  --  karma configuration

// if you import your existing 'webpack.config.js' setup here,
// be sure to read the note about 'entry' below.
const path = require('path')
const webpack_config = require('./webpack.config.js')

const webpack_test_config = {
  entry: './timesketch/ui/main.spec.ts',
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: ['ts-loader', 'angular2-template-loader'],
        exclude: /node_modules/,
      },
      {
        test: /\.s?css$/,
        use: 'null-loader',
      },
      {
        test: /\.html$/,
        loader: 'raw-loader',
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
    modules: [path.resolve(__dirname, 'timesketch/ui/'), 'node_modules'],
  },
}

module.exports = function(config) {
  config.set({

    files: [
      './node_modules/babel-polyfill/dist/polyfill.js',
      'timesketch/ui/main.spec.ts',
    ],
    preprocessors: {'timesketch/ui/main.spec.ts': ['webpack']},
    webpack: webpack_test_config,
    webpackMiddleware: {
      noInfo: true,
      stats: {chunks: false},
    },
    frameworks: ['jasmine'],
    plugins: [
      require('karma-webpack'),
      require('karma-jasmine'),
      require('karma-phantomjs-launcher'),
    ],
    browsers: ['PhantomJS'],
  })
}
