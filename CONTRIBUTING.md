### Contributing

#### Before you contribute

We love contributions! Read this page (including the small print at the end).

Before we can use your code, you must sign the [Google Individual Contributor License Agreement](https://developers.google.com/open-source/cla/individual?csw=1) (CLA), which you can do online. The CLA is necessary mainly because you own the copyright to your changes, even after your contribution becomes part of our codebase, so we need your permission to use and distribute your code. We also need to be sure of various other things—for instance that you'll tell us if you know that your code infringes on other people's patents. You don't have to sign the CLA until after you've submitted your code for review and a member has approved it, but you must do it before we can put your code into our codebase. Before you start working on a larger contribution, you should get in touch with us first through the issue tracker with your idea so that we can help out and possibly guide you. Coordinating up front makes it much easier to avoid frustration later on.

We use the github [fork and pull review process](https://help.github.com/articles/using-pull-requests) to review all contributions. First, fork the timesketch repository by following the [github instructions](https://help.github.com/articles/fork-a-repo). Then check out your personal fork:

    $ git clone https://github.com/<username>/timesketch.git

Add an upstream remote so you can easily keep up to date with the main repository:

    $ git remote add upstream https://github.com/google/timesketch.git

To update your local repo from the main:

    $ git pull upstream master

Please follow the Style Guide and make your changes. Once you're ready for review make sure the tests pass:

    $ yarn install
    $ python ./run_tests.py

Commit your changes to your personal fork and then use the GitHub Web UI to create and send the pull request. We'll review and merge the change.

#### Code review

All submissions, including submissions by project members, require review. To keep the code base maintainable and readable all code is developed using a similar coding style. It ensures:

The code is easy to maintain and understand. As a developer you'll sometimes find yourself thinking hmm, what is the code supposed to do here. It is important that you should be able to come back to code 5 months later and still quickly understand what it supposed to be doing. Also for other people that want to contribute it is necessary that they need to be able to quickly understand the code. Be that said, quick-and-dirty solutions might work in the short term, but we'll ban them from the code base to gain better long term quality.
With the code review process we ensure that at least two eyes looked over the code in hopes of finding potential bugs or errors (before they become bugs and errors). This also improves the overall code quality and makes sure that every developer knows to (largely) expect the same coding style.

Exception: Auto generated UI builds
PRs with only auto generated builds of the UI frontend (no new code) made by core project members (repo admins and maintainers with merge permissions) may be merged without review (by repo admins). Rational: All code in the build have already been reviewed.

#### Documentation review

One exception from the code review policy outlined above is simple documentation updates and additions made by core project members (repo admins and maintainers with merge permissions). These can be merged without review.

Note: Any change that affects the layout and structure of the site (timesketch.org) has to go through the review process and any update from external contributors has to be reviewed as well.

#### Style guide

We primarily follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html). Various Timesketch specific additions/variations are:

- Quote strings as ' or """ instead of "
- Textual strings should be Unicode strings and hence defined as u'string'
  Use the format() function instead of the %-way of formatting strings.
  Use positional or parameter format specifiers with typing e.g. '{0:s}' or '{text:s}' instead of '{0}', '{}' or '{:s}'. If we ever want to have language specific output strings we don't need to change the entire codebase. It also makes is easier in determining what type every parameter is expected to be.
- Use "cls" as the name of the class variable in preference of "klass"
- When catching exceptions use "as exception:" not some alternative form like "as error:" or "as details:"
- Use textual pylint overrides e.g. "# pylint: disable=no-self-argument" instead of "# pylint: disable=E0213". For a list of overrides see: http://docs.pylint.org/features.html

#### The small print

Contributions made by corporations are covered by a different agreement than
the one above, the Software Grant and Corporate Contributor License Agreement.
