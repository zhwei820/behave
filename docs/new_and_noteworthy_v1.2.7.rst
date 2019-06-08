Noteworthy in Version 1.2.7
==============================================================================

Summary:

* Support `Gherkin v6 grammar`_ (to simplify usage of `Example Mapping`_)
* Use/Support :pypi:`cucumber-tag-expressions` (superceed: old-style tag-expressions)
* :pypi:`cucumber-tag-expressions` are extended by "tag-matching"
  to match partial tag names, like: ``@foo.*``

.. _`Example Mapping`: https://cucumber.io/blog/example-mapping-introduction/
.. _`Example Mapping Webinar`: https://cucumber.io/blog/example-mapping-webinar/
.. _`Gherkin v6 grammar`: https://github.com/cucumber/cucumber/blob/master/gherkin/gherkin.berp



Support Gherkin v6 Grammar
-------------------------------------------------------------------------------

Grammar changes:

* ``Rule`` concept added to better correspond to `Example Mapping`_ concepts
* Add aliases for ``Scenario`` and ``Scenario Outline`` (for similar reasons)

A Rule (or: business rule) allows to group multiple Scenario(s)/Example(s)::

    # -- RULE GRAMMAR PSEUDO-CODE:
    @tag1 @tag2
    Rule: Optional Rule Title...
        Description?        #< CARDINALITY: 0..1 (optional)
        Background?         #< CARDINALITY: 0..1 (optional)
        Scenario*           #< CARDINALITY: 0..N (many)
        ScenarioOutline*    #< CARDINALITY: 0..N (many)

Gherkin v6 keyword aliases::

    | Concept          | Preferred Keyword | Alias(es)          |
    | Scenario         | Example           | Scenario           |
    | Scenario Outline | Scenario Outline  | Scenario Template  |

Example:

.. code-block:: gherkin

    # -- FILE: features/example_with_rules.feature
    # USING: Gherkin v6
    Feature: With Rules

      Background: Feature.Background
        Given feature background step_1

      Rule: Rule_1
        Background: Rule_1.Background
          Given rule_1 background step_1

        Example: Rule_1.Example_1
          Given rule_1 scenario_1 step_1

      Rule: Rule_2

        Example: Rule_2.Example_1
          Given rule_2 scenario_1 step_1

      Rule: Rule_3
        Background: Rule_3.EmptyBackground
        Example: Rule_3.Example_1
          Given rule_3 scenario_1 step_1

Overview of the `Example Mapping`_ concepts:

.. image:: _static/Cucumber_ExampleMapping.png
    :scale: 50 %
    :alt: Cucumber: `Example Mapping`_


.. seealso::

    **Gherkin v6**:

    * https://docs.cucumber.io/gherkin/reference/
    * `Gherkin v6 grammar`_

    **Example Mapping:**

    * Cucumber: Introduction to `Example Mapping`_ (by: Matt Wynne)
    * Cucumber: `Example Mapping Webinar`_
    * https://docs.cucumber.io/bdd/example-mapping/

    **More on Example Mapping:**

    * https://speakerdeck.com/mattwynne/rules-vs-examples-bddx-london-2014
    * https://lisacrispin.com/2016/06/02/experiment-example-mapping/
    * https://tobythetesterblog.wordpress.com/2016/05/25/how-to-do-example-mapping/

.. hint:: **Gherkin v6 Grammar Issues**

    * :cucumber.issue:`632`: Rule tags are currently only supported in `behave`.
      The Cucumber Gherkin v6 grammar currently lacks this functionality.

    * :cucumber.issue:`590`: Rule Background:
      A proposal is pending to remove Rule Backgrounds again


.. include:: _content.tag_expressions_v2.rst
