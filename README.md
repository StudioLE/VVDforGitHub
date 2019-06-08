# VVD for GitHub

VVD for GitHub identifies Dynamo and Grasshopper files that have been changed in the latest commit and generates a visual diff showing nodes and connectors that have been changed. 

VVD for GitHub is the missing piece in version control for Dynamo and Grasshopper.

*VVD ("Vivid") was originally built by Owen Derby, Michael Kirschner, Dan Taeyoung, and Andrew Heumann at the TT AEC Technology Hackathon 2015 in New York City. Learn more: [Presentation](https://github.com/oderby/VVD/blob/master/Presentation/Presi.pdf) / [GitHub Repository](https://github.com/oderby/VVD/)*

VVD for GitHub builds on their original work in order to integrate their visual graph diffing tool into an automated workflow for GitHub.

## How it works

VVD for GitHub is designed to be run on an automated build platform such as [AppVeyor](https://www.appveyor.com/) that is trigged when a file is commited to a repository containing Dynamo or Grasshopper files.

VVD for GitHub will:

1. Review changes in the latest commit and prepare a list of changed Dynamo and Grasshopper graphs.
2. Prepare the environment, install VVD and its dependencies.
3. Prepare the latest and previous versions of the files to be compared.
4. Create a `.diff` file comparing the latest and previous graphs using VVD
5. Create a PNG of the common graph `.diff` file showing a visual representation of the changes within the Dynamo or Grasshopper graph.

## Usage

In most scenarios you will just want the default action which runs all operations and functions in `vvd.py` in order.

```
python vvd.py
python vvd.py run
```

##### Helpers

To assist development additional helper operations have been included.

Review changes in the latest commit and return a list of changed Dynamo and Grasshopper graphs:

```
python vvd.py review
```

Prepare the environment, install VVD and its dependencies:

```
python vvd.py install
```

Prepare the latest and previous versions of the files to be compared.
Then, create a .diff file comparing the latest and previous graphs.
Then, create a PNG of the common graph .diff file:

```
python vvd.py diff --file example-1.3.4.dyn
python vvd.py diff --file example.gh
```