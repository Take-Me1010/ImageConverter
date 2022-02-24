# CONTRIBUTION

## コーディング規約

pylintとautopep8でlintingと整形。


## Pull Request

以下のようなプルリク歓迎

- 新たな画像変換の実装
- 処理の高速化

### 開発

[pipenv](https://github.com/pypa/pipenv)で開発しています。


```ps1
# pipenvで開発しています。
pipenv install --dev
# 仮想環境で開発して,,,
pipenv shell
# 追加できたらbuildコマンドでdist/main.pyに反映します。またrequirementも更新します。
pipenv run build
# test
pipenv run test
```
