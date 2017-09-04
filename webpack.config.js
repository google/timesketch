const path = require('path')
const ExtractTextPlugin = require('extract-text-webpack-plugin')
const AotPlugin = require('@ngtools/webpack').AotPlugin

const extractSass = new ExtractTextPlugin({
  filename: 'bundle.css',
  disable: false,
})

const aotPlugin = new AotPlugin({
  tsConfigPath: 'tsconfig.json',
  // entryModule path must be absolute, otherwise it generates really obscure
  // error message: https://github.com/angular/angular-cli/issues/4913
  entryModule: path.resolve(__dirname, 'timesketch/ui/app.module#AppModule'),
})

module.exports = {
  entry: './timesketch/ui/main.ts',
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: '@ngtools/webpack',
        exclude: /node_modules/,
      },
      {
        test: /\.s?css$/,
        use: extractSass.extract({
          use: [
            {loader: 'css-loader'},
            {loader: 'sass-loader'},
          ],
          fallback: 'style-loader'
        }),
      },
      {
        test: /\.woff(2)?(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'url-loader?limit=10000&mimetype=application/font-woff',
      },
      {
        test: /\.(ttf|eot|svg)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: 'file-loader',
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
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'timesketch/static/dist/'),
  },
  plugins: [extractSass, aotPlugin],
}
