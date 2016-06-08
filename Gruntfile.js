module.exports = function(grunt) {
  grunt.initConfig({
    sass: {
      dist: {
        options: {
          style: 'compressed',
          files: [{
            expand: true,
            cwd: 'styles',
            src: ['aqhi/static/sass/*.sass'],
            dest: 'aqhi/static/css',
            ext: '.css'
          }]
        }
      }
    },
    postcss: {
      options: {
        map: {
          inline: false,
          annotation: 'aqhi/static/css'
        },
        processors: [
          require('autoprefixer')({
            browsers: ['last 2 versions']
          })
        ]
      },
      dist: {
        src: 'aqhi/static/css/*.css'
      }
    },
    babel: {
      options: {
        sourceMap: true,
        presets: ['es2015']
      },
      dist: {
        files: {
          'aqhi/static/js/home-compiled.js': 'aqhi/static/js/home.js'
        }
      }
    },
    watch: {
      css: {
        files: ['aqhi/static/sass/*.sass'],
        tasks: ['sass', 'postcss']
      },
      babel: {
        files: 'aqhi/static/js/home.js',
        tasks: 'babel'
      }
    }
  });
  
  grunt.loadNpmTasks('grunt-postcss');
  grunt.loadNpmTasks('grunt-contrib-sass');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-babel');

  grunt.registerTask('default', ['sass', 'postcss']);
};