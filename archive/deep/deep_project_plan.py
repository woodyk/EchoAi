#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: deep_project_plan.py
# Author: [Your Name]
# Description: Deep Project Planning workflow that decomposes a project task into features,
# analyzes each feature, and synthesizes a comprehensive project plan document.
# Created: 2025-03-24
# Modified: 2025-03-24

from interactor import Interactor
import json

def deep_project_plan(project_task: str) -> str:
    # Instantiate the LLM interactor using your provided interact() function.
    #llm = Interactor(model="openai:gpt-4o-mini")
    llm = Interactor(model="ollama:llama3.2")
    
    # 1. Planning: Decompose the project task into a list of key features/components.
    planning_prompt = (
        f"Decompose the following software project task into a list of key features and components. "
        f"Include a brief high-level requirement for each feature:\n\n'{project_task}'"
    )
    planning_response = llm.interact(planning_prompt)
    features = parse_features(planning_response)
    
    project_sections = []
    
    # 2. For each feature, obtain detailed requirements and design considerations.
    for feature in features:
        detail_prompt = (
            f"Provide a detailed description for the feature '{feature}'. "
            "Include requirements, design considerations, potential challenges, and how it integrates "
            "with the overall project. Use examples where applicable."
        )
        detail_response = llm.interact(detail_prompt)
        section = f"### {feature}\n{detail_response}\n"
        project_sections.append(section)
    
    # 3. Synthesize the complete project plan document.
    synthesis_prompt = (
        f"Using the following detailed feature descriptions, create a comprehensive project plan "
        f"for the software project:\n\nProject Task: {project_task}\n\n"
        f"Features:\n" + "\n".join(project_sections) + "\n\n"
        "Now, compose a complete project plan document that includes an introduction, an overview of the "
        "project objectives, detailed sections for each feature with timelines and milestones where applicable, "
        "and a conclusion with next steps."
    )
    project_plan = llm.interact(synthesis_prompt)
    
    final_document = assemble_project_plan(project_plan)
    return final_document

def parse_features(response: str) -> list:
    """
    Parse the LLM response into a list of features.
    This placeholder function splits the response by lines and filters out empty lines.
    Modify as needed to suit the expected format.
    """
    # Example: split by newline and remove bullet markers.
    features = [line.strip("-• ") for line in response.splitlines() if line.strip()]
    return features

def assemble_project_plan(plan_content: str) -> str:
    """
    Assemble the final project plan document by adding a header and footer.
    """
    header = "# Project Plan Document\n\n"
    footer = "\n\n---\nEnd of Project Plan"
    return header + plan_content + footer

def main():
    print("Welcome to the Deep Project Planning Tool!")
    project_task = input("Enter the project task description: ")
    print("\nGenerating project plan...\n")
    plan = deep_project_plan(project_task)
    print("\nFinal Project Plan:\n")
    print(plan)

if __name__ == "__main__":
    main()

