@not_reproducible
@issue
Feature: Issue #457 -- Double-quotes in error messages of JUnit XML reports

    STATUS: Problem is currently not reproducible.
    XML attributes are escaped correctly even when double-quotes are used.

    @setup
    Scenario: Feature Setup
      Given a new working directory
      And a file named "features/steps/fail_steps.py" with:
        """
        from behave import step

        @step('{word:w} step fails with message')
        def step_fails(context, word):
            assert context.text
            assert False, "FAILED: "+ context.text

        @step('{word:w} step fails with error and message')
        def step_fails2(context, word):
            assert context.text
            raise RuntimeError(context.text)
        """


    Scenario: Use failing assertation in a JUnit XML report
      Given a file named "features/fails1.feature" with:
        """
        Feature:
          Scenario: Alice
            Given a step fails with message:
              '''
              My name is "Alice"
              '''
        """
      When I run "behave --junit features/fails1.feature"
      Then it should fail with:
        """
        0 scenarios passed, 1 failed, 0 skipped
        """
      And the file "reports/TESTS-fails1.xml" should contain:
        """
        <failure message="FAILED: My name is &quot;Alice&quot;"
        """

    Scenario: Use exception in a JUnit XML report
      Given a file named "features/fails2.feature" with:
        """
        Feature:
          Scenario: Bob
            Given a step fails with error and message:
              '''
              My name is "Bob" and <here> I am
              '''
        """
      When I run "behave --junit features/fails2.feature"
      Then it should fail with:
        """
        0 scenarios passed, 1 failed, 0 skipped
        """
      And the file "reports/TESTS-fails2.xml" should contain:
        """
        <error message="My name is &quot;Bob&quot; and &lt;here&gt; I am"
        """
